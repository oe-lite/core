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
import oelite.log
import oelite.process
import bb.utils

import sys
import os
import glob
import inspect
import re
from types import *
from pysqlite2 import dbapi2 as sqlite
from collections import Mapping
import random
import time
import multiprocessing

log = oelite.log.get_logger()


class CookBook(Mapping):

    #
    # The sqlite db should not need to be created before parsing recipe files,
    # as the parsing should only result in a pickled metadata file.  It might
    # still make sense to create it in __init__ though.
    #

    def __init__(self, baker):
        self.baker = baker # FIXME: get rid of this stored reference to baker
        self.config = baker.config
        self.parallel = baker.config.get('PARALLEL_PARSE')
        if self.parallel is None:
            self.parallel = multiprocessing.cpu_count()
        else:
            try:
                self.parallel = int(self.parallel)
            except ValueError:
                log.warning("invalid PARALLEL_PARSE value: %s", self.parallel)
                self.parallel = 0
            if self.parallel < 0:
                self.parallel = 0
        self.oeparser = baker.oeparser
        self.db = sqlite.connect(":memory:")
        if not self.db:
            raise Exception("could not create in-memory sqlite db")
        self.dbc = self.db.cursor()
        self.init_db()
        self.recipes = {}
        self.packages = {}
        self.tasks = {}
        self.session_signature = '%032x'%(random.getrandbits(128))
        self.debug = baker.debug
        fail = False
        recipe_files = self.list_recipefiles()
        total = len(recipe_files)
        count = 0
        to_parse = []
        log.debug("Checking for which recipes to parse")
        for recipe_file in recipe_files:
            cache = oelite.meta.cache.MetaCache(self.config, recipe_file)
            if not cache.is_current([self.config.env_signature()]):
                cache.clean()
                to_parse.append(recipe_file)
        timer = time.time()
        def factory(recipe, **kwargs):
            return oelite.recipe.RecipeParser(self, recipe, **kwargs)
        pool = oelite.process.Pool(factory, "Parsing recipe metadata")
        failed = pool.run(to_parse, parallel=self.parallel)
        if self.debug:
            log.debug("Parsing recipe metadata time %.3fs", time.time() - timer)

        if failed:
            for recipe, exitcode, logfile in failed:
                print '\nError:', oelite.path.relpath(recipe)
                with open(logfile, 'r') as logfile:
                    print logfile.read().strip()
            print '\nParse errors in %d recipes'%(len(failed))
            sys.exit(1)

        total = len(recipe_files)
        count = 0
        for recipe_file in recipe_files:
            oelite.util.progress_info(
               "Loading recipe summary information", total, count)
            count += 1
            log.debug("Loading %s", recipe_file)
            cache = oelite.meta.cache.MetaCache(self.config, recipe_file)
            if not cache.is_current([self.config.env_signature(),
                                     self.session_signature]):
                log.error("Stale metadata cache after parsing: %s",
                          cache.path)
                raise Exception()
            try:
                recipes = cache.load_recipes(self, meta=False)
            except Exception as e:
                log.error("Loading recipe cache failed: %s", cache.path)
                raise
            # the add_recipe method needs to be executed now ofcourse, but
            # using only the necessary information loaded from cache file.
            for recipe_type, recipe in recipes.items():
                oelite.pyexec.exechooks(recipe.meta, "pre_cookbook")
                self.add_recipe(recipe)
        oelite.util.progress_info(
            "Loading recipe summary information", total, count)

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
                dirfiles = find_recipefiles(f) # FIXME: not implemented!!
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


    def get_providers(self, type, item, recipe=None, version=None):
        #print "get_providers type=%s item=%s recipe=%s version=%s"%(
        #    repr(type), repr(item), repr(recipe), repr(version))
        select_from = "SELECT package.id FROM package,provide,recipe"
        select_where = "WHERE" + \
            " provide.package=package.id AND provide.item=:item" + \
            " AND package.recipe=recipe.id"
        if type:
            select_where += " AND package.type=:type"
        if recipe:
            select_where += " AND recipe.name=:recipe"
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

    def get_package_providers(self, item):
        item = self.item_id(item)
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT package FROM provide WHERE item=?", (item,)))


    def get_package_depends(self, package, deptypes):
        assert isinstance(package, oelite.package.OElitePackage)
        assert isinstance(deptypes, list) and len(deptypes) > 0
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT item FROM package_depend "
            "WHERE deptype IN (%s) "%(",".join("?" for i in deptypes)) +
            "AND package=?", (deptypes + [package.id])))
