from oebakery import die, err, warn, info, debug
import oebakery
from oelite import *
from oelite.dbutil import *
import oelite.parse
import oelite.util
from recipe import OEliteRecipe
from item import OEliteItem
import oelite.meta
import oelite.package
import oelite.path
import bb.utils
import oelite.profiling

import sys
import os
import glob
import inspect
import re
from types import *
from pysqlite2 import dbapi2 as sqlite
from collections import Mapping

class CookBook(Mapping):

    @oelite.profiling.profile_rusage_delta
    def __init__(self, baker):
        self.baker = baker
        self.config = baker.config
        self.oeparser = baker.oeparser
        self.init_layer_meta()
        self.db = sqlite.connect(":memory:")
        if not self.db:
            raise Exception("could not create in-memory sqlite db")
        self.db.text_factory = str
        self.dbc = self.db.cursor()
        self.init_db()
        self.recipes = {}
        self.packages = {}
        self.tasks = {}
        self.cachedir = self.config.get("CACHEDIR") or ""
        self.debug = self.baker.debug
        fail = False
        recipefiles = self.list_recipefiles()
        total = len(recipefiles)
        count = 0
        rusage = oelite.profiling.Rusage("recipe parsing")
        for recipefile in recipefiles:
            count += 1
            if self.debug:
                debug("Adding %s to cookbook [%s/%s]"%(
                        self.shortfilename(recipefile), count, total))
            else:
                oelite.util.progress_info("Adding recipes to cookbook",
                                          total, count)
            try:
                if not self.add_recipefile(recipefile):
                    fail = True
            except KeyboardInterrupt:
                if os.isatty(sys.stdout.fileno()) and not self.debug:
                    print
                die("Aborted while building cookbook")
            except oelite.parse.ParseError, e:
                if os.isatty(sys.stdout.fileno()) and not self.debug:
                    print
                e.print_details()
                err("Parse error in %s"%(self.shortfilename(recipefile)))
                fail = True
            except Exception, e:
                import traceback
                if os.isatty(sys.stdout.fileno()) and not self.debug:
                    print
                traceback.print_exc()
                err("Uncaught Python exception in %s"%(
                        self.shortfilename(recipefile)))
                fail = True
        rusage.end()
        if fail:
            die("Errors while adding recipes to cookbook")

        #print "when instantiating from a parsed oefile, do some 'finalizing', ie. collapsing of overrides and append, and remember to save expand_cache also"

        return

    def init_layer_meta(self):
        self.layer_meta = {}
        oepath = self.config.get('OEPATH').split(':')
        layer_priority = 0
        max_layer_height = 0
        def layer_height_roundup(priority):
            return (priority+99)/100*100
        layer_conf_files = []
        for layer in reversed(oepath):
            layer_conf = os.path.join(layer, 'conf', 'layer.conf')
            layer_meta = self.config.copy()
            if os.path.exists(layer_conf):
                self.oeparser.set_metadata(layer_meta)
                self.oeparser.reset_lexstate()
                layer_meta = self.oeparser.parse(layer_conf)
            layer_conf_files.append(layer_conf)
            priority_max = int(layer_meta.get('PRIORITY_MAX'))
            priority_min = int(layer_meta.get('PRIORITY_MIN'))
            layer_meta.set('LAYER_PRIORITY', layer_priority)
            assert priority_min < 0
            priority_baseline = (-priority_min) + 1
            layer_meta.set('PRIORITY_BASELINE', priority_baseline)
            layer_height = layer_height_roundup(priority_baseline + priority_max)
            layer_priority += layer_height
            max_layer_height = max(max_layer_height, layer_height)
            self.layer_meta[oelite.path.relpath(layer)] = layer_meta
        for layer in oepath:
            layer_meta = self.layer_meta[oelite.path.relpath(layer)]
            layer_meta.set('LAYER_NAME', oelite.path.relpath(layer) or '.')
            layer_meta.set('RECIPE_PREFERENCE_LAYER_PRIORITY',
                           layer_priority)
            layer_meta.set('PACKAGE_PREFERENCE_LAYER_PRIORITY',
                           layer_priority + max_layer_height)
            for layer_conf in layer_conf_files:
                layer_meta.set_input_mtime(layer_conf)
        return

    def new_recipe_meta(self, recipe):
        recipe_path = oelite.path.relpath(recipe)
        for layer in self.layer_meta:
            if not layer:
                continue
            if recipe_path.startswith(layer):
                return self.layer_meta[layer].copy()
        assert '' in self.layer_meta
        return self.layer_meta[''].copy()

    def __getitem__(self, key): # required by Mapping
        return self.recipes[key]

    def __len__(self): # required by Sized
        return len(self.recipes)

    def __iter__(self): # required by Iterable
        return self.recipes.__iter__()


    def init_db(self):

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS recipe ( "
            "id          INTEGER PRIMARY KEY, "
            "file        TEXT, "
            "type        TEXT, "
            "name        TEXT, "
            "version     TEXT, "
            "priority    INTEGER, "
            "UNIQUE (file, type) ON CONFLICT FAIL ) ")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS package ( "
            "id          INTEGER PRIMARY KEY, "
            "recipe      INTEGER, "
            "name        TEXT, "
            "type        TEXT, "
            "arch        TEXT, "
            "UNIQUE (recipe, name) ON CONFLICT ABORT )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task ( "
            "id          INTEGER PRIMARY KEY, "
            "recipe      INTEGER, "
            "name        TEXT, "
            "nostamp     INTEGER, "
            "UNIQUE (recipe, name) ON CONFLICT IGNORE ) ")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS recipe_depend ( "
            "recipe      INTEGER, "
            "deptype     TEXT, "
            "type        TEXT, "
            "item        TEXT, "
            "version     TEXT, "
            "UNIQUE (recipe, deptype, type, item) ON CONFLICT REPLACE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS provide ( "
            "package     INTEGER, "
            "item        TEXT, "
            "UNIQUE (package, item) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS package_depend ( "
            "package     INTEGER, "
            "deptype     TEXT, "
            "item        TEXT, "
            "UNIQUE (package, deptype, item) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_parent ( "
            "recipe      INTEGER, "
            "task        TEXT, "
            "parent      TEXT, "
            "UNIQUE (recipe, task, parent) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_deptask ( "
            "task        INTEGER, "
            "deptype     TEXT,"
            "deptask     TEXT, "
            "UNIQUE (task, deptype, deptask) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_recdeptask ( "
            "task        INTEGER, "
            "deptype     TEXT,"
            "recdeptask  TEXT, "
            "UNIQUE (task, deptype, recdeptask) ON CONFLICT IGNORE )")

        # Note: yes, we do want to keep this type of task
        # dependencies, although in OE-lite, you should NEVER EVER
        # depend on other task outputs than what is packaged, but it
        # can come in handy when automating some execution of some
        # specific tasks to be able to describe it in a a recipe.
        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_depend ( "
            "task        INTEGER, "
            "parent_item INTEGER, "
            "parent_task INTEGER )")

        return


    def get_recipe(self, id=None, task=None, package=None,
                   filename=None, type=None, name=None, version=None,
                   strict=True, default_type="machine"):
        """
        Get recipe from cookbook.  Returns recipe object if arguments
        match a single recipe.  Returns None if recipe is not found.
        Throws MultipleRecipes exception if more than one recipe is
        found.
        """
        recipes = self.get_recipes(
            id=id, task=task, package=package,
            filename=filename, type=type, name=name, version=version)

        if len(recipes) == 0:
            recipe = None
        elif len(recipes) == 1:
            recipe = recipes[0]
        elif strict:
            warn("multiple recipes found in %s.%s: returning None!"%(
                    self.__class__.__name__, inspect.stack()[0][3]))
            for recipe in recipes:
                info("%s:%s_%s"%(recipe.type, recipe.name, recipe.version))
            recipe = None
        else:
            chosen = [ recipes[0] ]
            for other in recipes[1:]:
                if chosen[0].priority > other.priority:
                    continue
                if chosen[0].priority < other.priority:
                    chosen = [ other ]
                    continue
                vercmp = bb.utils.vercmp_part(chosen[0].version, other.version)
                if vercmp < 0:
                    chosen = [ other ]
                if vercmp == 0:
                    #debug("chosen=%s\nother=%s"%(chosen, other))
                    #die("you have to be more precise")
                    chosen.append(other)
            if len(chosen) == 1:
                recipe = chosen[0]
            elif not default_type:
                warn("multiple recipes found in %s.%s: returning None!"%(
                        self.__class__.__name__, inspect.stack()[0][3]))
                for recipe in chosen:
                    info("%s:%s_%s"%(recipe.type, recipe.name, recipe.version))
                    recipe = None
            else:
                # there is multiple recipes with the same priority and version,
                # so let's try to pick the default type
                defaults_chosen = []
                for choice in chosen:
                    if choice.type == default_type:
                        defaults_chosen.append(choice)
                if len(defaults_chosen) == 1:
                    recipe = defaults_chosen[0]
                elif not defaults_chosen:
                    debug("multiple recipes, but none with default_type (%s)"%(
                            default_type))
                    recipe = None
                else:
                    warn("multiple recipes found in %s.%s: returning None!"%(
                            self.__class__.__name__, inspect.stack()[0][3]))
                    for recipe in defaults_chosen:
                        info("%s:%s_%s"%(recipe.type, recipe.name,
                                         recipe.version))
                    recipe = None

        return recipe


    def get_recipes(self, id=None, task=None, package=None,
                    filename=None, type=None, name=None, version=None):
        """
        Get recipes from cookbook.  Returns a list of recipe objects
        of the recipes found.  An empty list is returned if no recipes
        are found.
        """

        if id is not None:
            if isinstance(id, int):
                recipe_ids = [ (id,) ]
            else:
                recipe_ids = []
                for recipe_id in id:
                    recipe_ids.append((recipe_id,))

        elif task:
            assert isinstance(task, oelite.task.OEliteTask)
            recipe_ids = self.dbc.execute(
                "SELECT recipe FROM task WHERE id=?", (task.id,))

        elif package:
            if isinstance(package, oelite.package.OElitePackage):
                package = package.id
            assert isinstance(package, int)
            recipe_ids = self.dbc.execute(
                "SELECT recipe FROM package WHERE id=?", (package,))

        else:
            expr = []
            args = []
            if isinstance(name, oelite.item.OEliteItem):
                type = name.type
                version = name.version
                name = name.name
            if isinstance(filename, basestring):
                expr.append("file=?")
                args.append(filename)
            if isinstance(type, basestring):
                expr.append("type=?")
                args.append(type)
            if isinstance(name, OEliteItem):
                name = str(name)
            if isinstance(name, basestring):
                expr.append("name=?")
                args.append(name)
            if isinstance(version, basestring):
                expr.append("version=?")
                args.append(version)
            if not expr:
                raise ValueError("no arguments to runq.get_recipe_id ?")
            #print "expr = ",repr(expr)
            #print "args = ",repr(args)
            recipe_ids = self.dbc.execute(
                "SELECT id FROM recipe WHERE " + " AND ".join(expr), args)

        recipes = []
        for (recipe_id,) in recipe_ids:
            recipes.append(self.recipes[recipe_id])
        return recipes



    # FIXME: try to cleanup this mess, simplifying both package_id()
    # and get_package_id(), and hopefully getting rid of one of them.


    def package_id(self, package):
        raise Exception("deprecated package_id(%s)"%(repr(package)))


    def get_package(self, id=None, recipe=None, name=None, type=None, arch=None):
        """
        Get package from cookbook.  Returns package object if
        arguments match a single package.  Returns None if package is
        not found.  Throws MultiplePackages exception if more than one
        package is found.
        """
        packages = self.get_packages(id=id, recipe=recipe, name=name,
                                     type=type, arch=arch)
        if len(packages) == 1:
            package = packages[0]
        elif len(packages) == 0:
            package = None
        elif len(packages) > 1:
            warn("multiple packages found in %s.%s: returning None!"%(
                    self.__class__.__name__, inspect.stack()[0][3]))
            assert False
            package = None
        return package

    def get_packages(self, id=None, recipe=None, name=None, type=None, arch=None):
        query = "SELECT id, name, type, arch, recipe FROM package WHERE "
        if id is not None:
            if isinstance(id, int):
                where = "id=%d"%(id)
            elif len(id) == 1:
                where = "id=%d"%(id[0])
            else:
                package_ids = []
                for package_id in id:
                    package_ids.append(str(package_id))
                where = "id IN %s"%(repr(tuple(package_ids)))
            _packages = self.dbc.execute(query + where)
        else:
            expr = []
            args = []
            if isinstance(name, oelite.item.OEliteItem):
                type = name.type
                version = name.version
                name = name.name
            if recipe:
                expr.append("recipe=?")
                if isinstance(recipe, oelite.recipe.OEliteRecipe):
                    recipe = recipe.id
                args.append(recipe)
            if name:
                expr.append("name=?")
                args.append(name)
            if type:
                expr.append("type=?")
                args.append(type)
            if arch:
                expr.append("arch=?")
                args.append(arch)
            if not expr:
                raise ValueError("no arguments to cookbook.get_package_id")
            _packages = self.dbc.execute(query + " AND ".join(expr), args)

        packages = []
        for (id, name, type, arch, recipe) in _packages:
            try:
                packages.append(self.packages[id])
            except KeyError:
                self.packages[id] = oelite.package.OElitePackage(
                    id, name, type, arch, self.get_recipe(id=recipe))
                packages.append(self.packages[id])
        return packages


    # FIXME: remove
    def task_id(self, task):
        raise Exception("deprecated task_id(%s)"%(repr(task)))


    def get_task_id(self, recipe_id, task, strict=False):
        print "get_task_id task=%s"%(repr(task))
        assert isinstance(recipe_id, int)
        assert isinstance(task, str)
        task_id = flatten_single_value(self.dbc.execute(
                "SELECT id FROM task "
                "WHERE recipe=:recipe_id AND name=:task",
                locals()))
        if task_id is None and strict:
            raise NoSuchTask(task)
        return task_id


    def get_task_name(self, ontask):
        raise Exception(repr(task))


    def get_task(self, id=None, recipe=None, name=None, cookbook=None):
        tasks = self.get_tasks(id=id, recipe=recipe, name=name,
                               cookbook=cookbook)
        if len(tasks) == 0:
            return None
        elif len(tasks) > 1:
            raise MultipleTasks()
        return tasks[0]

    def get_tasks(self, id=None, recipe=None, name=None, cookbook=None):
        if id is not None:
            if isinstance(id, int):
                where = "id=%d"%(id)
            elif len(id) == 1:
                where = "id=%d"%(id[0])
            else:
                task_ids = []
                for task_id in id:
                    task_ids.append(str(task_id))
                task_ids = tuple(task_ids)
                where = "id IN %s"%(repr(tuple(task_ids)))
            _tasks = self.dbc.execute(
                "SELECT id, recipe, name, nostamp FROM task WHERE " + where)
        elif recipe and name:
            if isinstance(recipe, oelite.recipe.OEliteRecipe):
                recipe = recipe.id
            assert isinstance(recipe, int)
            if isinstance(name, str):
                _tasks = self.dbc.execute(
                    "SELECT id, recipe, name, nostamp FROM task "
                    "WHERE recipe=? AND name=?", (recipe, name))
            else:
                assert type(name) in (list, tuple)
                name = "('" + "','".join(name) + "')"
                _tasks = self.dbc.execute(
                    "SELECT id, recipe, name, nostamp FROM task "
                    "WHERE recipe=%s AND name IN %s"%(recipe, name))
        else:
            raise Exception("Invalid arguments to cookbook.get_tasks: recipe=%s name=%s"%(repr(recipe), repr(name)))

        tasks = []
        for (id, recipe, name, nostamp) in _tasks:
            try:
                tasks.append(self.tasks[id])
            except KeyError:
                self.tasks[id] = oelite.task.OEliteTask(
                    id, recipe, name, nostamp, self)
                tasks.append(self.tasks[id])
        return tasks





    def list_recipefiles(self, sort=True):
        OERECIPES = (self.config["OERECIPES"] or "").split(":")
        if not OERECIPES:
            die("OERECIPES not defined")
        files = []
        for f in OERECIPES:
            if os.path.isdir(f):
                dirfiles = find_recipoefiles(f)
                files.append(dirfiles)
            elif os.path.isfile(f):
                files.append(f)
            else:
                for file in glob.iglob(f):
                    files.append(file)

        oerecipes = []
        for f in files:
            if f.endswith(".oe"):
                oerecipes.append(f)
            else:
                warn("skipping %s: unknown file extension"%(f))

        if sort:
            oerecipes.sort()
        return oerecipes


    def shortfilename(self, filename):
        if filename.startswith(self.baker.topdir):
            return filename[len(self.baker.topdir):].lstrip("/")
        return filename


    def cachefilename(self, recipefile):
        recipefile = self.shortfilename(recipefile)
        return os.path.join(self.cachedir, recipefile + ".p")


    def add_recipefile(self, filename):
        cachefile = self.cachefilename(filename)

        recipes = None
        if os.path.exists(cachefile):
            try:
                meta_cache = oelite.meta.MetaCache(cachefile)
                if meta_cache.is_current(self.baker):
                    recipes = meta_cache.load(filename, self)
            except:
                print "Ignoring bad metadata cache:", cachefile

        if recipes is None:
            recipe_meta = self.parse_recipe(filename)
            if recipe_meta is False:
                print "ERROR: parsing %s failed"%(filename)
                return False
            if not recipe_meta:
                # recipe not compatible with our usage - pretend we've cached it
                return True
            recipes = {}
            is_cacheable = True
            for recipe_type in recipe_meta:
                recipe = OEliteRecipe(filename, recipe_type,
                                      recipe_meta[recipe_type], self)
                recipe.post_parse()
                recipes[recipe_type] = recipe
                is_cacheable = is_cacheable and recipe.is_cacheable()
            if is_cacheable:
                meta_cache = oelite.meta.MetaCache(cachefile, recipes,
                                                   self.baker)
            elif os.path.exists(cachefile):
                os.remove(cachefile)

        for recipe_type in recipes:
            oelite.pyexec.exechooks(recipes[recipe_type].meta,
                                    "pre_cookbook")
            self.add_recipe(recipes[recipe_type])

        return True


    def parse_recipe(self, recipe):
        #print "parsing recipe", recipe
        base_meta = self.new_recipe_meta(recipe)
        oelite.pyexec.exechooks(base_meta, "pre_recipe_parse")
        self.oeparser.set_metadata(base_meta)
        self.oeparser.reset_lexstate()
        base_meta = self.oeparser.parse(os.path.abspath(recipe))
        oelite.pyexec.exechooks(base_meta, "mid_recipe_parse")
        recipe_types = (base_meta.get("RECIPE_TYPES") or "").split()
        if not recipe_types:
            recipe_types = ["machine"]
        meta = {}
        for recipe_type in recipe_types:
            meta[recipe_type] = base_meta.copy()
        for recipe_type in recipe_types:
            meta[recipe_type]["RECIPE_TYPE"] = recipe_type
            self.oeparser.set_metadata(meta[recipe_type])
            self.oeparser.parse("classes/type/%s.oeclass"%(recipe_type))
            def arch_is_compatible(meta, arch_type):
                compatible_archs = meta.get("COMPATIBLE_%s_ARCHS"%arch_type)
                if compatible_archs is None:
                    return True
                arch = meta.get(arch_type + "_ARCH")
                for compatible_arch in compatible_archs.split():
                    if re.match(compatible_arch, arch):
                        return True
                debug("skipping %s_ARCH incompatible recipe %s:%s"%(
                    arch_type, recipe_type, meta.get("PN")))
                return False
            def cpu_families_is_compatible(meta, arch_type):
                compatible_cpu_fams = meta.get("COMPATIBLE_%s_CPU_FAMILIES"%arch_type)
                if compatible_cpu_fams is None:
                    return True
                cpu_fams = meta.get(arch_type + "_CPU_FAMILIES")
                if not cpu_fams:
                    return False
                for compatible_cpu_fam in compatible_cpu_fams.split():
                    for cpu_fam in cpu_fams.split():
                        if re.match(compatible_cpu_fam, cpu_fam):
                            return True
                debug("skipping %s_CPU_FAMILIES incompatible recipe %s:%s"%(
                    arch_type, recipe_type, meta.get("PN")))
                return False
            def machine_is_compatible(meta):
                compatible_machines = meta.get("COMPATIBLE_MACHINES")
                if compatible_machines is None:
                    return True
                machine = meta.get("MACHINE")
                if machine is None:
                    debug("skipping MACHINE incompatible recipe %s:%s"%(
                        recipe_type, meta.get("PN")))
                    return False
                for compatible_machine in compatible_machines.split():
                    if re.match(compatible_machine, machine):
                        return True
                debug("skipping MACHINE incompatible recipe %s:%s"%(
                    recipe_type, meta.get("PN")))
                return False
            def recipe_is_compatible(meta):
                incompatible_recipes = meta.get("INCOMPATIBLE_RECIPES")
                if incompatible_recipes is None:
                    return True
                pn = meta.get("PN")
                pv = meta.get("PV")
                for incompatible_recipe in incompatible_recipes.split():
                    if "_" in incompatible_recipe:
                        incompatible_recipe = incompatible_recipe.rsplit("_", 1)
                    else:
                        incompatible_recipe = (incompatible_recipe, None)
                    if not re.match("%s$"%(incompatible_recipe[0]), pn):
                        continue
                    if incompatible_recipe[1] is None:
                        return False
                    if re.match("%s$"%(incompatible_recipe[1]), pv):
                        debug("skipping incompatible recipe %s:%s_%s"%(
                            recipe_type, pn, pv))
                        return False
                return True
            def compatible_use_flags(meta):
                flags = meta.get("COMPATIBLE_IF_FLAGS")
                if not flags:
                    return True
                for name in flags.split():
                    val = meta.get("USE_"+name)
                    if not val:
                        debug("skipping %s:%s_%s (required %s USE flag not set)"%(
                                recipe_type, meta.get("PN"), meta.get("PV"),
                                name))
                        return False
                return True
            if ((not recipe_is_compatible(meta[recipe_type])) or
                (not machine_is_compatible(meta[recipe_type])) or
                (not arch_is_compatible(meta[recipe_type], "BUILD")) or
                (not arch_is_compatible(meta[recipe_type], "HOST")) or
                (not arch_is_compatible(meta[recipe_type], "TARGET"))):
                del meta[recipe_type]
                continue
            try:
                oelite.pyexec.exechooks(meta[recipe_type], "post_recipe_parse")
            except oelite.HookFailed, e:
                print "ERROR: %s:%s %s hook: %s"%(
                    recipe_type, base_meta.get("PN"), e.function, e.retval)
                return False
            if ((not compatible_use_flags(meta[recipe_type])) or
                (not cpu_families_is_compatible(meta[recipe_type], "BUILD")) or
                (not cpu_families_is_compatible(meta[recipe_type], "HOST")) or
                (not cpu_families_is_compatible(meta[recipe_type], "TARGET"))):
                del meta[recipe_type]
                continue
        return meta


    def add_recipe(self, recipe):
        self.dbc.execute(
            "INSERT INTO recipe "
            "(file, type, name, version, priority) "
            "VALUES (?, ?, ?, ?, ?)",
            (recipe.filename, recipe.type, recipe.name,
             recipe.version, recipe.priority))
        recipe_id = self.dbc.lastrowid
        recipe.set_id(recipe_id)
        self.recipes[recipe_id] = recipe

        task_names = recipe.get_task_names()
        taskseq = []
        for task_name in task_names:
            task_nostamp = recipe.meta.get_boolean_flag(task_name, "nostamp")
            taskseq.append((recipe_id, task_name, task_nostamp))
        if taskseq:
            self.dbc.executemany(
                "INSERT INTO task (recipe, name, nostamp) VALUES (?, ?, ?)",
                taskseq)

        for deptype in ("DEPENDS", "RDEPENDS", "FDEPENDS"):
            recipe_depends = []
            for item in (recipe.meta.get(deptype) or "").split():
                item = oelite.item.OEliteItem(item, (deptype, recipe.type))
                recipe_depends.append((recipe_id, deptype, item.type, item.name, item.version))
            for item in (recipe.meta.get("CLASS_"+deptype) or "").split():
                item = oelite.item.OEliteItem(item, (deptype, recipe.type))
                recipe_depends.append((recipe_id, deptype, item.type, item.name, item.version))
            if recipe_depends:
                self.dbc.executemany(
                    "INSERT INTO recipe_depend (recipe, deptype, type, item, version) "
                    "VALUES (?, ?, ?, ?, ?)", recipe_depends)

        for task_name in task_names:
            task_id = flatten_single_value(self.dbc.execute(
                    "SELECT id FROM task WHERE recipe=? AND name=?",
                    (recipe_id, task_name)))

            for parent in recipe.meta.get_list_flag(task_name, "deps"):
                self.dbc.execute(
                    "INSERT INTO task_parent (recipe, task, parent) "
                    "VALUES (:recipe_id, :task_name, :parent)",
                    locals())

            for _deptask in recipe.meta.get_list_flag(task_name, "deptask"):
                deptask = _deptask.split(":", 1)
                if len(deptask) != 2:
                    bb.fatal("invalid deptask:", _deptask)
                assert deptask[0] in ("DEPENDS", "RDEPENDS", "FDEPENDS")
                self.dbc.execute(
                    "INSERT INTO task_deptask (task, deptype, deptask) "
                    "VALUES (?, ?, ?)", ([task_id] + deptask))

            for _recdeptask in recipe.meta.get_list_flag(task_name,
                                                        "recdeptask"):
                recdeptask = _recdeptask.split(":", 1)
                if len(recdeptask) != 2:
                    bb.fatal("invalid deptask:", _recdeptask)
                assert recdeptask[0] in ("DEPENDS", "RDEPENDS", "FDEPENDS")
                self.dbc.execute(
                    "INSERT INTO task_recdeptask (task, deptype, recdeptask) "
                    "VALUES (?, ?, ?)", ([task_id] + recdeptask))

            for depends in recipe.meta.get_list_flag(task_name, "depends"):
                try:
                    (parent_item, parent_task) = depends.split(":")
                    self.dbc.execute(
                        "INSERT INTO task_depend "
                        "(task, parent_item, parent_task) "
                        "VALUES (?, ?, ?)",
                        (task_id, parent_item, parent_task))
                except ValueError:
                    err("invalid task 'depends' value for %s "
                        "(valid syntax is item:task): %s"%(
                            task_name, depends))

        packages = recipe.meta.get_list("PACKAGES")
        if not packages:
            warn("no packages defined for recipe %s"%(recipe))
        else:
            for package in packages:
                arch = (recipe.meta.get("PACKAGE_ARCH_" + package) or
                        recipe.meta.get("RECIPE_ARCH"))
                type = (recipe.meta.get("PACKAGE_TYPE_" + package) or
                        recipe.meta.get("RECIPE_TYPE"))
                package_id = self.add_package(recipe, package, type, arch)

                provides = recipe.meta.get("PROVIDES_" + package) or ""
                provides = provides.split()
                if not package in provides:
                    provides.append(package)
                for item in provides:
                    self.dbc.execute(
                        "INSERT INTO provide (package, item) "
                        "VALUES (?, ?)", (package_id, item))

                for deptype in ("DEPENDS", "RDEPENDS"):
                    depends = recipe.meta.get("%s_%s"%(deptype , package)) or ""
                    for item in depends.split():
                        self.dbc.execute(
                            "INSERT INTO package_depend "
                            "(package, deptype, item) "
                            "VALUES (?, ?, ?)", (package_id, deptype, item))

        return


    def add_package(self, recipe, name, type, arch):
        #print "add_package %s %s %s %s"%(recipe,name,type,arch)
        self.dbc.execute(
            "INSERT INTO package (recipe, name, type, arch) "
            "VALUES (?, ?, ?, ?)",
            (recipe.id, name, type, arch))
        return self.dbc.lastrowid


    def get_providers(self, type, item, version):
        select_from = "SELECT package.id FROM package,provide,recipe"
        select_where = "WHERE" + \
            " provide.package=package.id AND provide.item=:item" + \
            " AND package.recipe=recipe.id"
        if type:
            select_where += " AND package.type=:type"
        if version is not None:
            select_where += " AND recipe.version=:version"
        query = select_from + " " + select_where
        # Grrr... SQLite insists on sorting INTEGER colums as strings :-(
        #query += " ORDER BY recipe.name DESC"
        providers = self.dbc.execute(query, locals())
        providers = flatten_single_column_rows(providers)
        packages = self.get_packages(id=providers)
        def get_priority(p):
            return int(p.priority)
        packages = sorted(packages, key=get_priority, reverse=True)
        return packages


    def get_package_depends(self, package, deptype):
        assert isinstance(package, oelite.package.OElitePackage)
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT item FROM package_depend "
            "WHERE deptype=? "
            "AND package=?", (deptype, package.id)))

    def compute_recipe_build_priorities(self):
        recipes = self.recipes.values()
        # The dependencies are available as r.recipe_deps. We don't
        # need to mutate those sets for descendants computations, so
        # we just take an extra reference.
        parents = dict()
        children = dict()
        descendants = dict()
        for r in recipes:
            parents[r] = r.recipe_deps
            children[r] = set([])
            descendants[r] = set([r])
        for c in children:
            for p in parents[c]:
                children[p].add(c)
        childless = [r for r in children if len(children[r]) == 0]
        while childless:
            c = childless.pop()
            for p in parents[c]:
                descendants[p].update(descendants[c])
                children[p].remove(c)
                if not children[p]:
                    childless.append(p)
            c.build_prio = len(descendants[c])
            c.remaining_tasks = len(c.tasks)
            del descendants[c]
        assert(len(descendants) == 0)
