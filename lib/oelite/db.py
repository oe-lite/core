from oebakery import die, err, warn, info, debug
from oelite import *
from pysqlite2 import dbapi2 as sqlite
import inspect


class OEliteDB:

    def __init__(self):

        self.db = sqlite.connect(":memory:")
        if not self.db:
            raise Exception("could not create in-memory sqlite db")

        self.init_recipe_db()
        self.init_runq_db()

        return


    def init_recipe_db(self):
        c = self.db.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS recipe ( "
                  "id INTEGER PRIMARY KEY, "
                  "file TEXT, "
                  "extend TEXT, "
                  "name TEXT, "
                  "version TEXT, "
                  "preference INTEGER, "
                  "UNIQUE (file, extend) ON CONFLICT FAIL ) ")

        c.execute("CREATE TABLE IF NOT EXISTS package ( "
                  "id INTEGER PRIMARY KEY, "
                  "recipe INTEGER, "
                  "name TEXT, "
                  "arch TEXT, "
                  "UNIQUE (recipe, name) ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS item ( "
                  "id INTEGER PRIMARY KEY, "
                  "name TEXT UNIQUE ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS ritem ( "
                  "id INTEGER PRIMARY KEY, "
                  "name TEXT UNIQUE ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS task ( "
                  "id INTEGER PRIMARY KEY, "
                  "recipe INTEGER, "
                  "name INTEGER, "
                  "UNIQUE (recipe, name) ON CONFLICT IGNORE ) ")

        c.execute("CREATE TABLE IF NOT EXISTS task_name ( "
                  "id INTEGER PRIMARY KEY, "
                  "name TEXT UNIQUE ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS recipe_depend ( "
                  "recipe INTEGER, "
                  "item INTEGER, "
                  "UNIQUE (recipe, item) ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS recipe_rdepend ( "
                  "recipe INTEGER, "
                  "ritem INTEGER ,"
                  "UNIQUE (recipe, ritem) ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS package_provide ( "
                  "package INTEGER, "
                  "item INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS package_rprovide ( "
                  "package INTEGER, "
                  "ritem INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS package_depend ( "
                  "package INTEGER, "
                  "item INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS package_rdepend ( "
                  "package INTEGER, "
                  "ritem INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_parent ( "
                  "task INTEGER, "
                  "parent INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_deptask ( "
                  "task INTEGER, "
                  "deptask INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_rdeptask ( "
                  "task INTEGER, "
                  "rdeptask INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_recdeptask ( "
                  "task INTEGER, "
                  "recdeptask INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_recrdeptask ( "
                  "task INTEGER, "
                  "recrdeptask INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_depend ( "
                  "task INTEGER, "
                  "depend_item INTEGER, "
                  "depend_task INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_nostamp ( "
                  "task INTEGER UNIQUE )")

        self.db.commit()
        return


    def add_recipe(self, filename, extend, name, version, preference):
        self.db.execute(
            "INSERT INTO recipe "
            "(file, extend, name, version, preference) "
            "VALUES (:filename, :extend, :name, :version, :preference)",
            locals())
        # FIXME: do we need to add error handling for constraint violations?
        return


    def recipe_id(self, recipe):
        if isinstance(recipe, int):
            return recipe
        elif isinstance(recipe, tuple):
            recipe_id = self.get_recipe_id(*recipe)
        elif isinstance(recipe, dict):
            recipe_id = self.get_recipe_id(**recipe)
        else:
            raise ValueError("recipe=%s"%(recipe))
        if recipe_id is None:
            raise NoSuchRecipe(str(recipe))
        return recipe_id


    def get_recipe_id(self, filename=None, extend=None,
                      name=None, version=None,
                      task=None, package=None):
        if filename and (isinstance(extend, str) or
                         isinstance(extend, unicode)):
            recipe_id = self.db.execute(
                "SELECT id FROM recipe WHERE file=? AND extend=?",
                (filename, extend))
        elif name and version:
            recipe_id = self.db.execute(
                "SELECT id FROM recipe WHERE name=? AND version=?",
                (name, version))
        elif name:
            recipe_id = self.db.execute(
                "SELECT id FROM recipe WHERE name=?", (name,))
        elif task:
            task = self.task_id(task)
            recipe_id = self.db.execute(
                "SELECT recipe FROM task WHERE id=?", (task,))
        elif package:
            package = self.package_id(package)
            recipe_id = self.db.execute(
                "SELECT recipe FROM package WHERE id=?", (package,))
        else:
            raise ValueError(
                "invalid arguments: filename=%s extend=%s name=%s version=%s"%(
                    filename, extend, name, version))

        recipe_id = recipe_id.fetchall()
        if len(recipe_id) == 1:
            recipe_id = recipe_id[0][0]
        elif len(recipe_id) == 0:
            recipe_id = None
        elif len(recipe_id) > 1:
            warn("multiple recipes found in %s.%s: returning None!"%(
                    self.__class__.__name__, inspect.stack()[0][3]))
            recipe_id = None

        return recipe_id


    def get_recipe(self, recipe):
        recipe = self.recipe_id(recipe)
        return self.db.execute(
            "SELECT name, version FROM recipe WHERE id=?",
            (recipe,)).fetchone()


    def get_recipe_name(self, recipe):
        recipe = self.recipe_id(recipe)
        name = self.db.execute(
            "SELECT name, version FROM recipe WHERE id=?",
            (recipe,)).fetchone()
        if name is None:
            return None
        return "-".join(name)


    def get_recipes(self, recipes):
        if not recipes:
            return None
        recipes = list(recipes)
        for i in xrange(len(recipes)):
            recipes[i] = self.get_recipe(recipes[i])
        return recipes


    def add_package(self, recipe, name, arch):
        recipe = self.recipe_id(recipe)
        self.db.execute(
            "INSERT INTO package (recipe, name, arch) VALUES (?, ?, ?)",
            (recipe, name, arch))
        return


    def package_id(self, package):
        if isinstance(package, int):
            return package
        elif isinstance(package, tuple):
            package_id = self.get_package_id(*package)
        elif isinstance(package, dict):
            package_id = self.get_package_id(**package)
        else:
            raise ValueError("package=%s"%(package))
        if package_id is None:
            raise NoSuchPackage(str(package))
        return package_id


    def get_package_id(self, recipe=None, name=None):
        if recipe and name:
            recipe = self.recipe_id(recipe)
            package_id = self.db.execute(
                "SELECT id FROM package WHERE recipe=? AND name=?",
                (recipe, name))
        elif name:
            package_id = self.db.execute(
                "SELECT id FROM package WHERE name=?",
                (recipe, name))
        else:
            raise ValueError(
                "invalid arguments: recipe=%s name=%s"%(recipe, name))

        package_id = package_id.fetchall()
        if len(package_id) == 1:
            package_id = package_id[0][0]
        elif len(package_id) == 0:
            package_id = None
        elif len(package_id) > 1:
            warn("multiple packages found in %s.%s: returning None!"%(
                    self.__class__.__name__, inspect.stack()[0][3]))
            package_id = None

        return package_id


    def get_package(self, package):
        package = self.package_id(package)
        return self.db.execute(
            "SELECT name, arch FROM package WHERE id=?",
            (package,)).fetchone()


    def get_packages(self, packages):
        if not packages:
            return None
        packages = list(packages)
        for i in xrange(len(packages)):
            packages[i] = self.get_package(packages[i])
        return packages


    def add_item(self, item):
        self.db.execute(
            "INSERT INTO item (name) VALUES (?)", (item,))
        return


    def item_id(self, item):
        if isinstance(item, int):
            return item
        elif isinstance(item, str) or isinstance(item, unicode):
            item_id = self.get_item_id(item)
        else:
            raise ValueError("item=%s"%(item))
        if item_id is None:
            raise NoSuchItem(str(item))
        return item_id


    def get_item_id(self, item, auto_insert=True):
        item_id = self.db.execute(
            "SELECT id FROM item WHERE name=?", (item,)).fetchone()
        if item_id is None:
            if not auto_insert:
                return None
            self.add_item(item)
            return self.get_item_id(item, auto_insert=False)
        return item_id[0]


    def get_item(self, item_id):
        return flatten_one_string_row(self.db.execute(
            "SELECT name FROM item WHERE id=?", (item_id,)))


    def add_ritem(self, ritem):
        self.db.execute(
            "INSERT INTO ritem (name) VALUES (?)", (ritem,))
        return


    def ritem_id(self, ritem):
        if isinstance(ritem, int):
            return ritem
        elif isinstance(ritem, str) or isinstance(ritem, unicode):
            ritem_id = self.get_ritem_id(ritem)
        else:
            raise ValueError("ritem=%s"%(ritem))
        if ritem_id is None:
            raise NoSuchItem(str(ritem))
        return ritem_id


    def get_ritem_id(self, ritem, auto_insert=True):
        ritem_id = self.db.execute(
            "SELECT id FROM ritem WHERE name=?", (ritem,)).fetchone()
        if ritem_id is None:
            if not auto_insert:
                return None
            self.add_ritem(ritem)
            return self.get_ritem_id(ritem, auto_insert=False)
        return ritem_id[0]


    def get_ritem(self, ritem_id):
        ritem = self.db.execute(
            "SELECT name FROM ritem WHERE id=?", (ritem_id,)).fetchone()
        if ritem is None:
            return None
        return ritem[0]


    def add_task(self, recipe, name):
        recipe = self.recipe_id(recipe)
        name = self.task_name_id(name)
        self.db.execute(
            "INSERT INTO task (recipe, name) VALUES (?, ?)", (recipe, name))
        return


    def task_id(self, task):
        if isinstance(task, int):
            return task
        elif isinstance(task, tuple):
            task_id = self.get_task_id(*task)
        elif isinstance(task, dict):
            task_id = self.get_task_id(**task)
        else:
            import traceback
            traceback.print_stack()
            raise ValueError("task=%s"%(task))
        if task_id is None:
            raise NoSuchTask(str(task))
        return task_id


    def get_task_id(self, recipe, task):

        recipe = self.recipe_id(recipe)
        if recipe is None:
            return None

        task = self.task_name_id(task)
        if task is None:
            return None

        task_id = self.db.execute(
            "SELECT id FROM task "
            "WHERE recipe=:recipe AND name=:task",
            locals()).fetchone()
        if task_id is None:
            return None
        return task_id[0]


    def add_task_name(self, name):
        self.db.execute(
            "INSERT INTO task_name (name) VALUES (?)", (name,))
        return


    def get_task(self, name_id=None, task=None):
        if isinstance(name_id, int):
            name = self.db.execute(
                "SELECT name FROM task_name WHERE id=?",
                (name_id,))
        elif task:
            task = self.task_id(task)
            name = self.db.execute(
                "SELECT task_name.name FROM task, task_name "
                "WHERE task.id=? AND task.name=task_name.id",
                (task,))
        else:
            ValueError("name_id=%s, task=%s"%(name_id, task))
        return flatten_one_string_row(name)


    def task_name_id(self, name):
        if isinstance(name, int):
            return name
        elif isinstance(name, str) or isinstance(name, unicode):
            return self.get_task_name_id(name)
        raise ValueError("name=%s"%(name))


    def get_task_name_id(self, name, auto_insert=True):
        task_name_id = self.db.execute(
            "SELECT id FROM task_name WHERE name=:name",
            locals()).fetchone()
        if task_name_id is None:
            if not auto_insert:
                return None
            self.add_task_name(name)
            return self.get_task_name_id(name, auto_insert=False)
        return task_name_id[0]


    def add_recipe_depend(self, recipe, item):
        recipe = self.recipe_id(recipe)
        item = self.item_id(item)
        self.db.execute(
            "INSERT INTO recipe_depend (recipe, item) "
            "VALUES (:recipe, :item)", locals())
        return


    def get_recipe_depends(self, recipe):
        recipe = self.recipe_id(recipe)
        return flatten_single_column_rows(self.db.execute(
            "SELECT item FROM recipe_depend WHERE recipe=?", (recipe,)))


    def add_recipe_rdepend(self, recipe, ritem):
        recipe = self.recipe_id(recipe)
        ritem = self.ritem_id(ritem)
        self.db.execute(
            "INSERT INTO recipe_rdepend (recipe, ritem) "
            "VALUES (:recipe, :ritem)", locals())
        return


    def get_recipe_rdepends(self, recipe):
        recipe = self.recipe_id(recipe)
        return flatten_single_column_rows(self.db.execute(
            "SELECT ritem FROM recipe_rdepend WHERE recipe=?", (recipe,)))


    def add_provider(self, package, item):
        package = self.package_id(package)
        item = self.item_id(item)
        self.db.execute(
            "INSERT INTO package_provide (package, item) VALUES (?, ?)",
            (package, item))
        return


    def get_package_providers(self, item):
        item = self.item_id(item)
        return flatten_single_column_rows(self.db.execute(
            "SELECT package FROM package_provider WHERE item=?", (item,)))


    def add_rprovider(self, package, ritem):
        package = self.package_id(package)
        ritem = self.ritem_id(ritem)
        self.db.execute(
            "INSERT INTO package_rprovide (package, ritem) VALUES (?, ?)",
            (package, ritem))
        return


    def get_rproviders(self, ritem):
        ritem = self.item_id(ritem)
        return flatten_single_column_rows(self.db.execute(
            "SELECT package FROM package_rprovider WHERE ritem=?", (ritem,)))


    def add_package_depend(self, package, item):
        package = self.package_id(package)
        item = self.item_id(item)
        self.db.execute(
            "INSERT INTO package_depend (package, item) VALUES (?, ?)",
            (package, item))
        return


    def get_package_depends(self, package):
        package = self.package_id(package)
        return flatten_single_column_rows(self.db.execute(
            "SELECT item FROM package_depend WHERE package=?", (package,)))


    def add_package_rdepend(self, package, ritem):
        package = self.package_id(package)
        ritem = self.ritem_id(ritem)
        self.db.execute(
            "INSERT INTO package_rdepend (package, ritem) VALUES (?, ?)",
            (package, ritem))
        return


    def get_package_rdepends(self, package):
        package = self.package_id(package)
        return flatten_single_column_rows(self.db.execute(
            "SELECT ritem FROM package_rdepend WHERE package=?", (package,)))


    def add_task_parent(self, task, parent, recipe=None):
        task = self.task_id(task)
        if not recipe:
            recipe = self.get_recipe_id(task=task)
        parent = self.task_id((recipe, parent))
        self.db.execute(
            "INSERT INTO task_parent (task, parent) "
            "VALUES (?, ?)", (task, parent))
        return


    def get_task_parents(self, task):
        task = self.task_id(task)
        return flatten_single_column_rows(self.db.execute(
            "SELECT parent FROM task_parent WHERE task=?", (task,)))


    def add_task_deptask(self, task, deptask):
        task = self.task_id(task)
        deptask = self.task_name_id(deptask)
        self.db.execute(
            "INSERT INTO task_deptask (task, deptask) "
            "VALUES (?, ?)", (task, deptask))
        return


    def get_task_deptasks(self, task):
        task = self.task_id(task)
        return flatten_single_column_rows(self.db.execute(
            "SELECT deptask FROM task_deptask WHERE task=?", (task,)))


    def add_task_rdeptask(self, task, rdeptask):
        task = self.task_id(task)
        rdeptask = self.task_name_id(rdeptask)
        self.db.execute(
            "INSERT INTO task_rdeptask (task, rdeptask) "
            "VALUES (?, ?)", (task, rdeptask))
        return


    def get_task_rdeptasks(self, task):
        task = self.task_id(task)
        return flatten_single_column_rows(self.db.execute(
            "SELECT rdeptask FROM task_rdeptask WHERE task=?", (task,)))


    def add_task_recdeptask(self, task, recdeptask):
        task = self.task_id(task)
        recdeptask = self.task_name_id(recdeptask)
        self.db.execute(
            "INSERT INTO task_recdeptask (task, recdeptask) "
            "VALUES (?, ?)", (task, recdeptask))
        return


    def get_task_recdeptasks(self, task):
        task = self.task_id(task)
        return flatten_single_column_rows(self.db.execute(
            "SELECT recdeptask FROM task_recdeptask WHERE task=?", (task,)))


    def add_task_recrdeptask(self, task, recrdeptask):
        task = self.task_id(task)
        recrdeptask = self.task_name_id(recrdeptask)
        self.db.execute(
            "INSERT INTO task_recrdeptask (task, recrdeptask) "
            "VALUES (?, ?)", (task, recrdeptask))
        return


    def get_task_recrdeptasks(self, task):
        task = self.task_id(task)
        return flatten_single_column_rows(self.db.execute(
            "SELECT recrdeptask FROM task_recrdeptask WHERE task=?", (task,)))


    def add_task_depend(self, task, depend_item, depend_task):
        task_id = self.task_id(task)
        depend_item_id = self.item_id(depend_item)
        depend_task_id = self.task_name_id(depend_task)
        self.db.execute(
            "INSERT INTO task_depend (task, depend_item, depend_task) "
            "VALUES (?, ?, ?)", (task_id, depend_item_id, depend_task_id))
        return


    def get_task_depends(self, task):
        task = self.task_id(task)
        return self.db.execute(
            "SELECT depend_item AS item, depend_task AS task "
            "FROM task_depend WHERE task=?", (task,)).fetchall()


    def set_task_nostamp(self, task):
        task_id = self.task_id(task)
        self.db.execute(
            "INSERT INTO task_nostamp (task) VALUES (?)", (task_id,))
        return


    def is_task_nostamp(self, task):
        task = self.task_id(task)
        nostamp = self.db.execute(
            "SELECT task FROM task_nostamp WHERE task=?", (task,)).fetchone()
        return bool(nostamp)


    def init_runq_db(self):
        c = self.db.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS runq_provider ( "
                  "item INTEGER, "
                  "package INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS runq_rprovider ( "
                  "ritem INTEGER, "
                  "package INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS runq_task ( "
                  "task INTEGER, "
                  "hash TEXT, "
                  "dephash TEXT, "
                  "datahash TEXT, "
                  "srchash TEXT, " # srchash only needs to be
                                   # considered in do_fetch, as it
                                   # will then propagate through the
                                   # dependency chain
                  "status INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS runq_taskdepend ( "
                  "task INTEGER, "
                  "depend INTEGER )") # depend is task id

        c.execute("CREATE TABLE IF NOT EXISTS runq_recdepend_recipe ( "
                  "package INTEGER, "
                  "depend INTEGER )") # depend is recipe id

        c.execute("CREATE TABLE IF NOT EXISTS runq_recdepend_package ( "
                  "package INTEGER, "
                  "depend INTEGER )") # depend is package id

        c.execute("CREATE TABLE IF NOT EXISTS runq_recrdepend_recipe ( "
                  "package INTEGER, "
                  "rdepend INTEGER )") # rdepend is recipe id

        c.execute("CREATE TABLE IF NOT EXISTS runq_recrdepend_package ( "
                  "package INTEGER, "
                  "rdepend INTEGER )") # rdepend is package id

        return


    def number_of_runq_tasks(self):
        return flatten_single_value(self.db.execute(
                "SELECT COUNT(*) FROM runq_task"))


    def set_runq_provider(self, item, package):
        item = self.item_id(item)
        package = self.package_id(package)
        self.db.execute(
            "INSERT INTO runq_provider (item, package) VALUES (?, ?)",
            (item, package)).fetchone()
        return


    def get_runq_provider(self, item):
        item = self.item_id(item)
        runq_provider = self.db.execute(
            "SELECT package FROM runq_provider WHERE item=?",
            (item,)).fetchone()
        if runq_provider is None:
            return None
        return runq_provider[0]


    def get_providers(self, item, recipe=None, version=None):
        item = self.item_id(item)
        if item and recipe and version:
            providers = self.db.execute(
                "SELECT package.id, "
                "recipe.name, recipe.version, recipe.preference "
                "FROM package, package_provide, recipe "
                "WHERE package_provide.item=:item "
                "AND recipe.name=:recipe AND recipe.version=:version "
                "AND package.recipe=recipe.id "
                "AND package_provide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        elif item and recipe:
            providers = self.db.execute(
                "SELECT package.id, "
                "recipe.name, recipe.version, recipe.preference "
                "FROM package, package_provide, recipe "
                "WHERE package_provide.item=:item "
                "AND recipe.name=:recipe "
                "AND package.recipe=recipe.id "
                "AND package_provide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        else:
            providers = self.db.execute(
                "SELECT package.id, "
                "recipe.name, recipe.version, recipe.preference "
                "FROM package, package_provide, recipe "
                "WHERE package_provide.item=:item "
                "AND package.recipe=recipe.id "
                "AND package_provide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        return providers.fetchall()


    def set_runq_rprovider(self, ritem, package):
        ritem = self.ritem_id(ritem)
        package = self.package_id(package)
        self.db.execute(
            "INSERT INTO runq_rprovider (ritem, package) VALUES (?, ?)",
            (ritem, package)).fetchone()
        return


    def get_runq_rprovider(self, ritem):
        ritem = self.ritem_id(ritem)
        runq_rprovider = self.db.execute(
            "SELECT package FROM runq_rprovider WHERE ritem=?",
            (ritem,)).fetchone()
        if runq_rprovider is None:
            return None
        return runq_rprovider[0]


    def get_rproviders(self, ritem, recipe=None, version=None):
        ritem = self.ritem_id(ritem)
        if ritem and recipe and version:
            rproviders = self.db.execute(
                "SELECT package.id, "
                "recipe.name, recipe.version, recipe.preference "
                "FROM package, package_rprovide, recipe "
                "WHERE package_rprovide.ritem=:ritem "
                "AND recipe.name=:recipe AND recipe.version=:version "
                "AND package.recipe=recipe.id "
                "AND package_rprovide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        elif ritem and recipe:
            rproviders = self.db.execute(
                "SELECT package.id, recipe.preference, recipe.version "
                "FROM package, package_rprovide, recipe "
                "WHERE package_rprovide.ritem=:ritem "
                "AND recipe.name=:recipe "
                "AND package.recipe=recipe.id "
                "AND package_rprovide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        else:
            rproviders = self.db.execute(
                "SELECT package.id, recipe.preference, recipe.version "
                "FROM package, package_rprovide, recipe "
                "WHERE package_rprovide.ritem=:ritem "
                "AND package.recipe=recipe.id "
                "AND package_rprovide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        return rproviders.fetchall()


    def add_runq_task(self, task):
        task = self.task_id(task)
        self.db.execute(
            "INSERT INTO runq_task (task) VALUES (?)", (task,))
        return


    def add_runq_tasks(self, tasks):
        tasklist = []
        for task in tasks:
            tasklist.append((task,))
        self.db.executemany(
            "INSERT INTO runq_task (task) VALUES (?)", (tasklist))
        return


    def add_runq_taskdepend(self, task, depend):
        task = self.task_id(task)
        depend = self.task_id(depend)
        self.db.execute(
            "INSERT INTO runq_taskdepend (task, depend) VALUES (?, ?)",
            (task, depend))
        return


    def add_runq_taskdepends(self, task, depends):
        task = self.task_id(task)
        if isinstance(depends, set):
            depends = list(depends)
        for i in range(len(depends)):
            depends[i] = (task, self.task_id(depends[i]))
        self.db.executemany(
            "INSERT INTO runq_taskdepend (task, depend) VALUES (?, ?)",
            depends)
        return


    def set_runq_recdepends(self, package, recipes, packages):
        #debug("set_runq_recdepends package=%s recipes=%s packages=%s"%(
        #        self.get_package(package),
        #        self.get_recipes(recipes),
        #        self.get_packages(packages)))
        package = self.package_id(package)
        recipelist = []
        for depend in recipes:
            recipelist.append((package, depend))
        self.db.executemany(
            "INSERT INTO runq_recdepend_recipe (package, depend) "
            "VALUES (?, ?)", recipelist)
        packagelist = []
        for depend in packages:
            packagelist.append((package, depend))
        self.db.executemany(
            "INSERT INTO runq_recdepend_package (package, depend) "
            "VALUES (?, ?)", packagelist)
        return


    def get_runq_recdepends(self, package):
        package = self.package_id(package)
        recipes = flatten_single_column_rows(self.db.execute(
                "SELECT depend FROM runq_recdepend_recipe WHERE package=?",
                (package,)))
        packages = flatten_single_column_rows(self.db.execute(
                "SELECT depend FROM runq_recdepend_package WHERE package=?",
                (package,)))
        #debug("get_runq_recdepends package=%s recipes=%s packages=%s"%(
        #        self.get_package(package),
        #        self.get_recipes(recipes),
        #        self.get_packages(packages)))
        return (recipes, packages)


    def set_runq_recrdepends(self, package, recipes, packages):
        #debug("set_runq_recdepends package=%s recipes=%s packages=%s"%(
        #        self.get_package(package),
        #        self.get_recipes(recipes),
        #        self.get_packages(packages)))
        package = self.package_id(package)
        recipelist = []
        for rdepend in recipes:
            recipelist.append((package, rdepend))
        self.db.executemany(
            "INSERT INTO runq_recrdepend_recipe (package, rdepend) "
            "VALUES (?, ?)", recipelist)
        packagelist = []
        for rdepend in packages:
            packagelist.append((package, rdepend))
        self.db.executemany(
            "INSERT INTO runq_recrdepend_package (package, rdepend) "
            "VALUES (?, ?)", packagelist)
        return


    def get_runq_recrdepends(self, package):
        package = self.package_id(package)
        recipes = flatten_single_column_rows(self.db.execute(
                "SELECT rdepend FROM runq_recrdepend_recipe WHERE package=?",
                (package,)))
        packages = flatten_single_column_rows(self.db.execute(
                "SELECT rdepend FROM runq_recrdepend_package WHERE package=?",
                (package,)))
        #debug("get_runq_recrdepends package=%s recipes=%s packages=%s"%(
        #        self.get_package(package),
        #        self.get_recipes(recipes),
        #        self.get_packages(packages)))
        return (recipes, packages)


    def get_readytasks(self):
        return flatten_single_column_rows(self.db.execute(
                "SELECT task FROM runq_task WHERE NOT EXISTS "
                "(SELECT * FROM runq_taskdepend"
                " WHERE runq_taskdepend.task = runq_task.task) "
                "AND status IS NULL"))


    def get_hashabletasks(self):
        return flatten_single_column_rows(self.db.execute(
                "SELECT task FROM runq_task "
                "WHERE hash IS NULL AND NOT EXISTS "
                "(SELECT runq_taskdepend.task "
                " FROM runq_taskdepend, runq_task AS runq_task_depend"
                " WHERE runq_taskdepend.task = runq_task.task"
                " AND runq_taskdepend.depend = runq_task_depend.task"
                " AND runq_task_depend.hash IS NULL )"))


    def _set_runq_task_status(self, task, status):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET status=? WHERE task=?", (status, task))
        return


    def set_runq_task_pending(self, task):
        return self._set_runq_task_status(task, 1)


    def set_runq_task_running(self, task):
        return self._set_runq_task_status(task, 2)


    def set_runq_task_failed(self, task):
        return self._set_runq_task_status(task, 4)


    def set_runq_task_done(self, task, delete):
        task = self.task_id(task)
        self._set_runq_task_status(task, 3)
        if delete:
            self.db.execute(
                "DELETE FROM runq_taskdepend WHERE depend=?", (task,))
        return


    def prune_done_tasks(self):
        self.db.execute(
            "DELETE FROM runq_taskdepend WHERE EXISTS "
            "( SELECT * FROM runq_task "
            "WHERE runq_task.task = runq_taskdepend.depend AND status=3 )")
        return


    def get_runq_task_hash(self, task):
        task = self.task_id(task)
        return flatten_single_value(self.db.execute(
            "SELECT hash FROM runq_task WHERE task=?", (task,)))


    def set_runq_task_hash(self, task, dephash):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET hash=? WHERE task=?",
            (dephash, task))
        return




def flatten_single_value(rows):
    row = rows.fetchone()
    if row is None:
        return None
    return row[0]


def flatten_one_string_row(rows):
    row = rows.fetchone()
    if row is None:
        return None
    return str(row[0])


def flatten_single_column_rows(rows):
    rows = rows.fetchall()
    if not rows:
        return []
    for i in range(len(rows)):
        rows[i] = rows[i][0]
    return rows
