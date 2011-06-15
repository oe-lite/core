from oebakery import die, err, warn, info, debug
from oelite import *
from oelite.dbutil import *
from recipe import OEliteRecipe
from item import OEliteItem
import oelite.meta
import oelite.package
import bb.utils

import sys
import os
import glob
import inspect
from types import *
from pysqlite2 import dbapi2 as sqlite
from collections import Mapping


class CookBook(Mapping):


    def __init__(self, baker):
        self.baker = baker
        self.config = baker.config
        self.bbparser = baker.bbparser
        self.db = sqlite.connect(":memory:")
        if not self.db:
            raise Exception("could not create in-memory sqlite db")
        self.dbc = self.db.cursor()
        self.init_db()
        self.recipes = {}
        self.packages = {}
        self.tasks = {}
        self.cachedir = self.config.get("CACHEDIR") or ""
        for recipefile in self.list_recipefiles():
            self.add_recipefile(recipefile)

        #print "when instantiating from a parsed bbfile, do some 'finalizing', ie. collapsing of overrides and append, and remember to save expand_cache also"

        return


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
            "type        TEXT, "
            "item        TEXT, "
            "UNIQUE (recipe, type, item) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS recipe_rdepend ( "
            "recipe      INTEGER, "
            "type        TEXT, "
            "item        TEXT, "
            "UNIQUE (recipe, type, item) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS provide ( "
            "package     INTEGER, "
            "item        TEXT, "
            "UNIQUE (package, item) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS package_depend ( "
            "package     INTEGER, "
            "type        TEXT, "
            "item        TEXT, "
            "UNIQUE (package, type, item) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS package_rdepend ( "
            "package     INTEGER, "
            "type        TEXT, "
            "item        TEXT, "
            "UNIQUE (package, type, item) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_parent ( "
            "task        INTEGER, "
            "parent      INTEGER, "
            "UNIQUE (task, parent) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_deptask ( "
            "task        INTEGER, "
            "deptask     TEXT, "
            "UNIQUE (task, deptask) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_rdeptask ( "
            "task        INTEGER, "
            "rdeptask    TEXT, "
            "UNIQUE (task, rdeptask) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_recdeptask ( "
            "task        INTEGER, "
            "recdeptask  TEXT, "
            "UNIQUE (task, recdeptask) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_recrdeptask ( "
            "task        INTEGER, "
            "recrdeptask TEXT, "
            "UNIQUE (task, recrdeptask) ON CONFLICT IGNORE )")

        self.dbc.execute(
            "CREATE TABLE IF NOT EXISTS task_recadeptask ( "
            "task        INTEGER, "
            "recadeptask TEXT, "
            "UNIQUE (task, recadeptask) ON CONFLICT IGNORE )")

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
            assert isinstance(name, str)
            _tasks = self.dbc.execute(
                "SELECT id, recipe, name, nostamp FROM task "
                "WHERE recipe=? AND name=?", (recipe, name))
        else:
            raise Exception("Invalid arguments to cookbook.get_tasks")

        tasks = []
        for (id, recipe, name, nostamp) in _tasks:
            try:
                tasks.append(self.tasks[id])
            except KeyError:
                self.tasks[id] = oelite.task.OEliteTask(
                    id, recipe, name, nostamp, self)
                tasks.append(self.tasks[id])
        return tasks





    def list_recipefiles(self):
        BBRECIPES = (self.config["BBRECIPES"] or "").split(":")
        if not BBRECIPES:
            die("BBRECIPES not defined")
        files = []
        for f in BBRECIPES:
            if os.path.isdir(f):
                dirfiles = find_recipoefiles(f)
                files.append(dirfiles)
            elif os.path.isfile(f):
                files.append(f)
            else:
                for file in glob.iglob(f):
                    files.append(file)

        bbrecipes = []
        #bbappend = []
        for f in files:
            if f.endswith(".bb"):
                bbrecipes.append(f)
            #elif f.endswith(".bbappend"):
            #    bbappend.append(f)
            else:
                warn("skipping %s: unknown file extension"%(f))

        #appendlist = {}
        #for f in bbappend:
        #    base = os.path.basename(f).replace(".bbappend", ".bb")
        #    if not base in appendlist:
        #        appendlist[base] = []
        #    appendlist[base].append(f)

        return bbrecipes


    def cachefilename(self, recipefile):
        if recipefile.startswith(self.baker.topdir):
            recipefile = recipefile[len(self.baker.topdir):]
        return os.path.join(self.cachedir, recipefile.lstrip("/") + ".p")


    def add_recipefile(self, filename):
        cachefile = self.cachefilename(filename)

        recipes = None
        if os.path.exists(cachefile):
            meta_cache = oelite.meta.MetaCache(cachefile)
            if meta_cache.is_current():
                recipes = meta_cache.load(filename, self)

        if not recipes:
            recipe_meta = self.parse_recipe(filename)
            recipes = {}
            
            for recipe_type in recipe_meta:
                recipe = OEliteRecipe(filename, recipe_type,
                                      recipe_meta[recipe_type], self)
                recipe.post_parse()
                recipes[recipe_type] = recipe
            meta_cache = oelite.meta.MetaCache(cachefile, recipes)

        for recipe_type in recipes:
            oelite.pyexec.exechooks(recipes[recipe_type].meta,
                                    "pre_cookbook")
            self.add_recipe(recipes[recipe_type])

        return


    def parse_recipe(self, recipe):
        base_meta = self.config.copy()
        oelite.pyexec.exechooks(base_meta, "pre_recipe_parse")
        self.bbparser.set_metadata(base_meta)
        self.bbparser.reset_lexstate()
        base_meta = self.bbparser.parse(os.path.abspath(recipe))
        oelite.pyexec.exechooks(base_meta, "mid_recipe_parse")
        recipe_types = (base_meta.get("RECIPE_TYPES") or "").split()
        if not recipe_types:
            #raise Exception("No RECIPE_TYPES!")
            recipe_types = (["machine"] +
                            (base_meta.get("BBCLASSEXTEND") or "").split())
        meta = {}
        #meta[recipe_types[0]] = base_meta
        #for recipe_type in recipe_types[1:]:
        for recipe_type in recipe_types:
            meta[recipe_type] = base_meta.copy()
        for recipe_type in recipe_types:
            meta[recipe_type]["RECIPE_TYPE"] = recipe_type
            self.bbparser.set_metadata(meta[recipe_type])
            #print "parsing recipe_type %s"%(recipe_type)
            #print "classes/type/%s.bbclass"%(recipe_type)
            self.bbparser.parse("classes/type/%s.bbclass"%(recipe_type))
            oelite.pyexec.exechooks(meta[recipe_type], "post_recipe_parse")
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

        recipe_depends = []
        for item in (recipe.meta.get("DEPENDS") or "").split():
            recipe_depends.append((recipe_id, item))
        if recipe_depends:
            self.dbc.executemany(
                "INSERT INTO recipe_depend (recipe, item) "
                "VALUES (?, ?)", recipe_depends)

        recipe_rdepends = []
        for item in (recipe.meta.get("RDEPENDS") or "").split():
            recipe_rdepends.append((recipe_id, item))
        if recipe_rdepends:
            self.dbc.executemany(
                "INSERT INTO recipe_depend (recipe, item) "
                "VALUES (?, ?)", recipe_rdepends)

        for task_name in task_names:
            task_id = flatten_single_value(self.dbc.execute(
                    "SELECT id FROM task WHERE recipe=? AND name=?",
                    (recipe_id, task_name)))
            # FIXME: find out how to use this prefetched task_id in the
            # INSERT-SELECT statements below

            for parent in recipe.meta.get_list_flag(task_name, "deps"):
                self.dbc.execute(
                    "INSERT INTO task_parent (task, parent) "
                    "SELECT task.id, parent.id "
                    "FROM task, task as parent "
                    "WHERE"
                    "  task.name=:task_name AND task.recipe=:recipe_id"
                    "  AND"
                    "  parent.name=:parent AND parent.recipe=:recipe_id",
                    locals())

            for deptask in recipe.meta.get_list_flag(task_name, "deptask"):
                self.dbc.execute(
                    "INSERT INTO task_deptask (task, deptask) "
                    "VALUES (?, ?)", (task_id, deptask))

            for rdeptask in recipe.meta.get_list_flag(task_name, "rdeptask"):
                self.dbc.execute(
                    "INSERT INTO task_rdeptask (task, rdeptask) "
                    "VALUES (?, ?)", (task_id, rdeptask))

            for recdeptask in recipe.meta.get_list_flag(task_name,
                                                        "recdeptask"):
                self.dbc.execute(
                    "INSERT INTO task_recdeptask (task, recdeptask) "
                    "VALUES (?, ?)", (task_id, recdeptask))

            for recrdeptask in recipe.meta.get_list_flag(task_name,
                                                         "recrdeptask"):
                self.dbc.execute(
                    "INSERT INTO task_recrdeptask (task, recrdeptask) "
                    "VALUES (?, ?)", (task_id, recrdeptask))

            for recadeptask in recipe.meta.get_list_flag(task_name,
                                                         "recadeptask"):
                self.dbc.execute(
                    "INSERT INTO task_recadeptask (task, recadeptask) "
                    "VALUES (?, ?)", (task_id, recadeptask))

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
                for item in provides.split():
                    self.dbc.execute(
                        "INSERT INTO provide (package, item) "
                        "VALUES (?, ?)", (package_id, item))
            
                depends = recipe.meta.get("DEPENDS_" + package) or ""
                for item in depends.split():
                    self.dbc.execute(
                        "INSERT INTO package_depend (package, item) "
                        "VALUES (?, ?)", (package_id, item))
            
                rdepends = recipe.meta.get("RDEPENDS_" + package) or ""
                for item in rdepends.split():
                    self.dbc.execute(
                        "INSERT INTO package_rdepend (package, item) "
                        "VALUES (?, ?)", (package_id, item))


        return


    def add_package(self, recipe, name, type, arch):
        self.dbc.execute(
            "INSERT INTO package (recipe, name, type, arch) "
            "VALUES (?, ?, ?, ?)",
            (recipe.id, name, type, arch))
        return self.dbc.lastrowid


    def get_providers(self, type, item, recipe=None, version=None):
        if recipe and version:
            providers = self.dbc.execute(
                "SELECT package.id "
                #"recipe.name, recipe.version, recipe.priority "
                "FROM package, provide, recipe "
                "WHERE provide.item=:item "
                "AND recipe.name=:recipe AND recipe.version=:version "
                "AND package.recipe=recipe.id "
                "AND provide.package=package.id "
                "AND package.type=:type "
                "ORDER BY recipe.priority DESC, recipe.name", locals())
        elif recipe:
            providers = self.dbc.execute(
                "SELECT package.id "
                #"recipe.name, recipe.version, recipe.priority "
                "FROM package, provide, recipe "
                "WHERE provide.item=:item "
                "AND recipe.name=:recipe "
                "AND package.recipe=recipe.id "
                "AND provide.package=package.id "
                "AND package.type=:type "
                "ORDER BY recipe.priority DESC, recipe.name", locals())
        else:
            providers = self.dbc.execute(
                "SELECT package.id "
                #"recipe.name, recipe.version, recipe.priority "
                "FROM package, provide, recipe "
                "WHERE provide.item=:item "
                "AND package.recipe=recipe.id "
                "AND provide.package=package.id "
                "AND package.type=:type "
                "ORDER BY recipe.priority DESC, recipe.name", locals())

        return self.get_packages(id=flatten_single_column_rows(providers))
                                 

    def get_package_providers(self, item):
        item = self.item_id(item)
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT package FROM provide WHERE item=?", (item,)))


    def get_package_depends(self, package):
        assert isinstance(package, oelite.package.OElitePackage)
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT item FROM package_depend WHERE package=?", (package.id,)))


    def get_package_rdepends(self, package):
        assert isinstance(package, oelite.package.OElitePackage)
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT item FROM package_rdepend WHERE package=?", (package.id,)))
