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

        c.execute("CREATE TABLE IF NOT EXISTS task_recadeptask ( "
                  "task INTEGER, "
                  "recadeptask INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS task_depend ( "
                  "task INTEGER, "
                  "parent_item INTEGER, "
                  "parent_task INTEGER )")

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
                      task=None, package=None, multiple=False):
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
            if not multiple:
                recipe_id = recipe_id[0][0]
            else:
                recipe_id = [ recipe_id[0][0] ]
        elif len(recipe_id) == 0:
            recipe_id = None
        elif len(recipe_id) > 1:
            if not multiple:
                warn("multiple recipes found in %s.%s: returning None!"%(
                        self.__class__.__name__, inspect.stack()[0][3]))
                for r in recipe_id:
                    info(self._get_recipe_name(r[0]))
                recipe_id = None
            else:
                recipe_id = map(tuple_to_var, recipe_id)

        return recipe_id


    def get_recipe(self, recipe):
        recipe = self.recipe_id(recipe)
        return self.db.execute(
            "SELECT name, version FROM recipe WHERE id=?",
            (recipe,)).fetchone()


    def get_recipe_name(self, recipe):
        recipe = self.recipe_id(recipe)
        return self._get_recipe_name(recipe)


    def _get_recipe_name(self, recipe):
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
                (name,))
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


    def add_task_recadeptask(self, task, recadeptask):
        task = self.task_id(task)
        recdeptask = self.task_name_id(recadeptask)
        self.db.execute(
            "INSERT INTO task_recadeptask (task, recadeptask) "
            "VALUES (?, ?)", (task, recadeptask))
        return


    def get_task_recadeptasks(self, task):
        task = self.task_id(task)
        return flatten_single_column_rows(self.db.execute(
            "SELECT recadeptask FROM task_recadeptask WHERE task=?", (task,)))


    def add_task_depend(self, task, parent_item, parent_task):
        task_id = self.task_id(task)
        parent_item_id = self.item_id(parent_item)
        parent_task_id = self.task_name_id(parent_task)
        self.db.execute(
            "INSERT INTO task_depend (task, parent_item, parent_task) "
            "VALUES (?, ?, ?)", (task_id, parent_item_id, parent_task_id))
        return


    def get_task_depends(self, task):
        task = self.task_id(task)
        return self.db.execute(
            "SELECT parent_item AS item, parent_task AS task "
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
                  "prime INTEGER, "
                  "build INTEGER, "
                  "relax INTEGER, "
                  "status INTEGER, "
                  "metahash TEXT, "
                  "mtime REAL, "
                  "tmphash TEXT, "
                  "buildhash TEXT, "
                  "UNIQUE (task) ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS runq_depend ( "
                  "id INTEGER PRIMARY KEY, "
                  "task INTEGER, "
                  "prime INTEGER, "
                  "parent_task INTEGER, " #
                  "depend_package INTEGER DEFAULT -1, "
                  "rdepend_package INTEGER DEFAULT -1, "
                  "filename TEXT, "
                  "prebake INTEGER, "
                  "UNIQUE (task, parent_task, depend_package, rdepend_package) "
                  "ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS runq_recdepend ( "
                  "package INTEGER, "
                  "parent_recipe INTEGER, "
                  "parent_package INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS runq_recrdepend ( "
                  "package INTEGER, "
                  "parent_recipe INTEGER, "
                  "parent_package INTEGER )")

        return


    def get_recipes_with_tasks_to_build(self):
        recipes = []
        for row in self.db.execute(
            "SELECT DISTINCT task.recipe "
            "FROM runq_task, task "
            "WHERE runq_task.build IS NOT NULL "
            "AND runq_task.task=task.id"):
            row[0]
            r = self.db.execute(
                "SELECT recipe.id, recipe.name, recipe.version, "
                "COUNT(runq_task.build) "
                "FROM runq_task, task, recipe "
                "WHERE recipe.id=? "
                "AND runq_task.task=task.id AND task.recipe=recipe.id ",
                (row[0],))
            recipes.append(r.fetchone())
        return recipes
       

    def print_runq_tasks(self):
        runq_tasks = self.db.execute(
            "SELECT prime,build,status,relax,metahash,tmphash,mtime,task from runq_task").fetchall()
        for row in runq_tasks:
            for col in row:
                print "%s "%(col),
            print "%s:%s"%(self.get_recipe_name({"task":row[7]}),
                           self.get_task(task=row[7]))
        return


    def print_runq_depends(self):
        runq_depends = self.db.execute(
            "SELECT prime,task,parent_task,parent_package,parent_rpackage FROM runq_depend").fetchall()
        for row in runq_depends:
            prime = row[0] or 0
            print "%d %4d -> %4d %4s %4s  %s:%s -> %s:%s"%(
                prime, row[1], row[2], row[3], row[4],
                self.get_recipe_name({"task":row[1]}),
                self.get_task(task=row[1]),
                self.get_recipe_name({"task":row[2]}),
                self.get_task(task=row[2]))
        return

    def number_of_runq_tasks(self):
        return flatten_single_value(self.db.execute(
                "SELECT COUNT(*) FROM runq_task"))


    def number_of_tasks_to_build(self):
        return flatten_single_value(self.db.execute(
                "SELECT COUNT(*) FROM runq_task WHERE build IS NOT NULL"))


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
                "SELECT package.id, "
                "recipe.name, recipe.version, recipe.preference "
                "FROM package, package_rprovide, recipe "
                "WHERE package_rprovide.ritem=:ritem "
                "AND recipe.name=:recipe "
                "AND package.recipe=recipe.id "
                "AND package_rprovide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        else:
            rproviders = self.db.execute(
                "SELECT package.id, "
                "recipe.name, recipe.version, recipe.preference "
                "FROM package, package_rprovide, recipe "
                "WHERE package_rprovide.ritem=:ritem "
                "AND package.recipe=recipe.id "
                "AND package_rprovide.package=package.id "
                "ORDER BY recipe.preference DESC, recipe.name", locals())
        return rproviders.fetchall()


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


    def add_runq_task(self, task):
        task = self.task_id(task)
        self.db.execute(
            "INSERT INTO runq_task (task) VALUES (?)", (task,))
        return


    def add_runq_tasks(self, tasks):
        tasks = map(var_to_tuple, tasks)
        self.db.executemany(
            "INSERT INTO runq_task (task) VALUES (?)", (tasks))
        return


    def add_runq_depend(self, task, depend,
                        depend_package=None, rdepend_package=None):
        task = self.task_id(task)
        depend = self.task_id(depend)
        if depend_package:
            package = self.package_id(depend_package)
            task_name = self.get_task(task=task)
            recipe_name = self.get_recipe_name({"task": task})
            self.db.execute(
                "INSERT INTO runq_depend (task, parent_task, depend_package) "
                "VALUES (?, ?, ?)", (task, depend, package))
        elif rdepend_package:
            package = self.package_id(rdepend_package)
            self.db.execute(
                "INSERT INTO runq_depend (task, parent_task, rdepend_package) "
                "VALUES (?, ?, ?)", (task, depend, package))
        else:
            self.db.execute(
                "INSERT INTO runq_depend (task, parent_task) "
                "VALUES (?, ?)", (task, depend))
        return


    def add_runq_task_depends(self, task, depends):
        task = self.task_id(task)
        def task_tuple(depend):
            return (task, depend)
        values = map(task_tuple, depends)
        self.db.executemany(
            "INSERT INTO runq_depend (task, parent_task) VALUES (?, ?)", values)
        return


    def add_runq_package_depends(self, task, depends):
        if not depends:
            return
        task = self.task_id(task)
        for depend in depends:
            self.add_runq_depend(task, depend[0], depend_package=depend[1])

    def add_runq_package_rdepends(self, task, depends):
        if not depends:
            return
        task = self.task_id(task)
        for depend in depends:
            self.add_runq_depend(task, depend[0], rdepend_package=depend[1])


    def set_runq_package_filename(self, package, filename, prebake=False):
        package = self.package_id(package)
        if prebake:
            self.db.execute(
                "UPDATE runq_depend SET filename=?, prebake=1 "
                "WHERE depend_package=? OR rdepend_package=?",
                (filename, package, package))
        else:
            self.db.execute(
                "UPDATE runq_depend SET filename=? "
                "WHERE depend_package=? OR rdepend_package=?",
                (filename, package, package))
        return


    def prune_prebaked_runq_depends(self):

        tasks = flatten_single_column_rows(self.db.execute(
            "SELECT"
            "  task "
            "FROM"
            "  runq_task "
            "WHERE"
            "  EXISTS " # something depends on it
            "    (SELECT *"
            "     FROM runq_depend"
            "     WHERE parent_task=runq_task.task"
            "     LIMIT 1)"
            "  AND NOT EXISTS " # and no task-based dependencies on it
            "    (SELECT * FROM runq_depend "
            "     WHERE runq_depend.parent_task=runq_task.task"
            "     AND (runq_depend.depend_package < 0 AND"
            "          runq_depend.rdepend_package < 0)"
            "     LIMIT 1)"
            "  AND NOT EXISTS " # and no non-prebaked dependencies on it
            "    (SELECT *"
            "     FROM runq_depend"
            "     WHERE runq_depend.parent_task=runq_task.task"
            "     AND (runq_depend.depend_package >= 0 OR"
            "          runq_depend.rdepend_package >= 0)"
            "     AND runq_depend.prebake IS NULL"
            "     LIMIT 1)"
            ))

        for task in tasks:
            debug("prebaked %s:%s"%(self.get_recipe_name({"task": task}),
                                    self.get_task(task=task)))
            self.db.execute(
                "UPDATE runq_depend SET parent_task=NULL WHERE parent_task=?",
                (task,))

        return        


    def get_runq_package_filename(self, package):
        package = self.package_id(package)
        return flatten_single_value(self.db.execute(
                "SELECT filename "
                "FROM runq_depend "
                "WHERE depend_package=? OR rdepend_package=? "
                "LIMIT 1", (package, package)))


    def set_runq_recdepends(self, package, recdepends):
        return self._set_runq_recdepends(
            package, recdepends, "runq_recdepend")

    def set_runq_recrdepends(self, package, recrdepends):
        return self._set_runq_recdepends(
            package, recrdepends, "runq_recrdepend")

    def _set_runq_recdepends(self, package, recdepends, runq_recdepend):
        if not recdepends:
            return
        package = self.package_id(package)
        def task_tuple(depend):
            return (package, depend[0], depend[1])
        recdepends = map(task_tuple, recdepends)
        self.db.executemany(
            "INSERT INTO %s "%(runq_recdepend) +
            "(package, parent_recipe, parent_package) "
            "VALUES (?, ?, ?)", recdepends)
        return


    def get_runq_recdepends(self, package):
        return self._get_runq_recdepends(package, "runq_recdepend")

    def get_runq_recrdepends(self, package):
        return self._get_runq_recdepends(package, "runq_recrdepend")

    def _get_runq_recdepends(self, package, runq_recdepend):
        package = self.package_id(package)
        return self.db.execute(
                "SELECT parent_recipe, parent_package "
                "FROM %s "%(runq_recdepend) +
                "WHERE package=?", (package,)).fetchall()


    def get_readytasks(self):
        return flatten_single_column_rows(self.db.execute(
                "SELECT"
                "  task "
                "FROM"
                "  runq_task "
                "WHERE"
                "  build=1 AND status IS NULL AND NOT EXISTS"
                "  (SELECT * FROM runq_depend"
                "   WHERE runq_depend.task=runq_task.task"
                "   AND runq_depend.parent_task IS NOT NULL"
                "   LIMIT 1)"))


    def get_metahashable_tasks(self):
        return flatten_single_column_rows(self.db.execute(
                "SELECT task FROM runq_task "
                "WHERE metahash IS NULL AND NOT EXISTS "
                "(SELECT runq_depend.task"
                " FROM runq_depend, runq_task AS runq_task_depend"
                " WHERE runq_depend.task = runq_task.task"
                " AND runq_depend.parent_task = runq_task_depend.task"
                " AND runq_task_depend.metahash IS NULL"
                " LIMIT 1"
                ")"))


    def get_runq_package_metahash(self, package):
        package = self.package_id(package)
        return flatten_single_value(self.db.execute(
                "SELECT"
                "  runq_task.metahash "
                "FROM"
                "  runq_task, runq_depend "
                "WHERE"
                "  runq_depend.parent_task=runq_task.task"
                "  AND (runq_depend.depend_package=? OR"
                "       runq_depend.rdepend_package=?)"
                "  LIMIT 1", (package, package)))


    def get_runq_package_metahash(self, package):
        return self._get_runq_package_hash(package, "metahash")

    def get_runq_package_buildhash(self, package):
        return self._get_runq_package_hash(package, "buildhash")

    def _get_runq_package_hash(self, package, hash):
        package = self.package_id(package)
        return flatten_single_value(self.db.execute(
                "SELECT"
                "  runq_task.%s "
                "FROM"
                "  runq_task, runq_depend "
                "WHERE"
                "  runq_depend.parent_task=runq_task.task"
                "  AND (runq_depend.depend_package=? OR"
                "       runq_depend.rdepend_package=?) "
                "LIMIT 1"%(hash),
                (package, package)))


    def get_runq_depend_packages(self, task=None):
        if task:
            task = self.task_id(task)
            return flatten_single_column_rows(self.db.execute(
                    "SELECT DISTINCT depend_package "
                    "FROM runq_depend "
                    "WHERE depend_package >= 0 AND task=?",
                (task,)))
        else:
            return flatten_single_column_rows(self.db.execute(
                    "SELECT DISTINCT depend_package "
                    "FROM runq_depend "
                    "WHERE depend_package >= 0"))


    def get_runq_rdepend_packages(self, task=None):
        if task:
            task = self.task_id(task)
            return flatten_single_column_rows(self.db.execute(
                    "SELECT DISTINCT rdepend_package "
                    "FROM runq_depend "
                    "WHERE rdepend_package >= 0 AND task=?",
                (task,)))
        else:
            return flatten_single_column_rows(self.db.execute(
                    "SELECT DISTINCT rdepend_package "
                    "FROM runq_depend "
                    "WHERE rdepend_package >= 0"))


    def get_runq_packages_to_build(self):
        depend_packages = flatten_single_column_rows(self.db.execute(
                "SELECT DISTINCT depend_package "
                "FROM runq_depend "
                "WHERE depend_package >= 0 AND prebake IS NULL"))
        rdepend_packages = flatten_single_column_rows(self.db.execute(
                "SELECT DISTINCT rdepend_package "
                "FROM runq_depend "
                "WHERE rdepend_package >= 0 AND prebake IS NULL"))
        return set(depend_packages).union(rdepend_packages)


    def set_runq_buildhash_for_build_tasks(self):
        rowcount = self.db.execute(
            "UPDATE runq_task SET buildhash=metahash WHERE build=1"
            ).rowcount
        if rowcount == -1:
            die("unable to determine rowcount in "
                "set_runq_buildhash_for_build_tasks")
        return rowcount


    def set_runq_buildhash_for_nobuild_tasks(self):
        rowcount = self.db.execute(
            "UPDATE runq_task SET buildhash=tmphash WHERE build IS NULL"
            ).rowcount
        if rowcount == -1:
            die("unable to determine rowcount in "
                "set_runq_buildhash_for_nobuild_tasks")
        return rowcount


    def mark_primary_runq_depends(self):
        rowcount = self.db.execute(
            "UPDATE runq_depend SET prime=1 WHERE EXISTS "
            "(SELECT * FROM runq_task"
            " WHERE runq_task.prime=1 AND runq_task.task=runq_depend.task"
            ")").rowcount
        if rowcount == -1:
            die("mark_primary_runq_depends did not work out")
        return rowcount


    def prune_runq_depends_nobuild(self):
        c = self.db.cursor()
        rowcount = 0
        while c.rowcount:
            c.execute(
                "UPDATE runq_depend SET parent_task=NULL "
                "WHERE parent_task IS NOT NULL AND NOT EXISTS "
                "(SELECT * FROM runq_task"
                " WHERE runq_task.build=1"
                " AND runq_task.task=runq_depend.parent_task"
                " LIMIT 1"
                ")")
            if rowcount == -1:
                die("prune_runq_depends_nobuild did not work out")
            rowcount += c.rowcount
        if rowcount:
            debug("pruned %d dependencies that did not have to be rebuilt"%rowcount)
        return rowcount


    def prune_runq_depends_with_nobody_depending_on_it(self):
        c = self.db.cursor()
        rowcount = 0
        while c.rowcount:
            c.execute(
                "DELETE FROM runq_depend "
                "WHERE prime IS NULL AND NOT EXISTS "
                "(SELECT * FROM runq_depend AS next_depend"
                " WHERE next_depend.parent_task=runq_depend.task"
                " LIMIT 1"
                ")")
            if rowcount == -1:
                die("prune_runq_depends_with_no_depending_tasks did not work out")
            rowcount += c.rowcount
        if rowcount:
            debug("pruned %d dependencies which where not needed anyway"%rowcount)
        return rowcount


    def prune_runq_tasks(self):
        rowcount = self.db.execute(
            "UPDATE"
            "  runq_task "
            "SET"
            "  build=NULL "
            "WHERE"
            "  prime IS NULL AND NOT EXISTS"
            "  (SELECT *"
            "   FROM runq_depend"
            "   WHERE runq_depend.parent_task=runq_task.task"
            "   LIMIT 1"
            ")").rowcount
        if rowcount == -1:
            die("prune_runq_tasks did not work out")
        if rowcount:
            debug("pruned %d tasks that does not need to be build"%rowcount)
        return rowcount


    def set_runq_task_stamp(self, task, mtime, tmphash):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET mtime=?, tmphash=? WHERE task=?",
            (mtime, tmphash, task))
        return


    def set_runq_task_build(self, task):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET build=1 WHERE task=?", (task,))
        return


    def set_runq_task_relax(self, task):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET relax=1 WHERE task=?", (task,))
        return


    def set_runq_task_primary(self, task):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET prime=1 WHERE task=?", (task,))
        return


    def is_runq_task_primary(self, task):
        task = self.task_id(task)
        primary = self.db.execute(
            "SELECT prime FROM runq_task WHERE task=?", (task,)).fetchone()
        return primary[0] == 1


    def is_runq_recipe_primary(self, recipe):
        recipe = self.recipe_id(recipe)
        primary = self.db.execute(
            "SELECT runq_task.prime "
            "FROM runq_task, task "
            "WHERE task.recipe=? AND runq_task.prime IS NOT NULL "
            "AND runq_task.task=task.id", (recipe,)).fetchone()
        return primary and primary[0] == 1


    def set_runq_task_build_on_nostamp_tasks(self):
        rowcount = self.db.execute(
            "UPDATE runq_task SET build=1 "
            "WHERE build IS NULL AND EXISTS "
            "(SELECT * FROM task_nostamp"
            " WHERE task_nostamp.task=runq_task.task)").rowcount
        if rowcount == -1:
            die("set_runq_task_build_on_nostamp_tasks did not work out")
        debug("set build flag on %d nostamp tasks"%(rowcount))
        return


    def set_runq_task_build_on_retired_tasks(self):
        c = self.db.cursor()
        rowcount = 0
        while c.rowcount:
            c.execute(
                "UPDATE runq_task SET build=1 "
                "WHERE build IS NULL AND EXISTS "
                "(SELECT * FROM runq_depend, runq_task AS parent_task"
                " WHERE runq_depend.task=runq_task.task"
                " AND runq_depend.parent_task=parent_task.task"
                " AND parent_task.mtime > runq_task.mtime)")
            if rowcount == -1:
                die("set_runq_task_build_on_retired_tasks did not work out")
            rowcount += c.rowcount
        debug("set build flag on %d retired tasks"%(rowcount))
        return


    def set_runq_task_build_on_hashdiff(self):
        c = self.db.cursor()
        rowcount = 0
        while c.rowcount:
            c.execute(
                "UPDATE runq_task SET build=1 "
                "WHERE build IS NULL AND relax IS NULL AND tmphash != metahash")
            rowcount += c.rowcount
        debug("set build flag on %d tasks with tmphash != metahash"%(rowcount))
        #hest = c.execute("SELECT metahash,tmphash FROM runq_task").fetchall()
        #info("hest=%s"%(repr(hest)))
        return


    def propagate_runq_task_build(self):
        """always build all tasks depending on other tasks to build"""
        c = self.db.cursor()
        rowcount = 0
        while c.rowcount:
            c.execute(
                "UPDATE"
                "  runq_task "
                "SET"
                "  build=1 "
                "WHERE"
                "  build IS NULL"
                "  AND EXISTS"
                "    (SELECT *"
                "     FROM runq_depend, runq_task AS parent_task"
                "     WHERE runq_depend.task=runq_task.task"
                "     AND runq_depend.parent_task=parent_task.task"
                "     AND parent_task.build=1"
                "     LIMIT 1)")
            rowcount += c.rowcount
        debug("set build flag on %d tasks due to propagation"%(rowcount))
        return


    def _set_runq_task_status(self, task, status):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET status=? WHERE task=?", (status, task))
        return


    def set_runq_task_pending(self, task):
        return self._set_runq_task_status(task, 1)


    def set_runq_task_running(self, task):
        return self._set_runq_task_status(task, 2)


    def set_runq_task_done(self, task, delete):
        task = self.task_id(task)
        self._set_runq_task_status(task, 3)
        #if delete:
        #    self.db.execute(
        #        "DELETE FROM runq_depend WHERE parent_task=?", (task,))
        self.db.execute(
            "UPDATE runq_depend SET parent_task=NULL "
            "WHERE parent_task=?", (task,))
        return


    def set_runq_task_failed(self, task):
        return self._set_runq_task_status(task, -1)


    def prune_done_tasks(self):
        self.db.execute(
            "DELETE FROM runq_depend WHERE EXISTS "
            "( SELECT * FROM runq_task "
            "WHERE runq_task.task = runq_depend.parent_task AND status=3 )")
        return


    def set_runq_task_metahash(self, task, metahash):
        task = self.task_id(task)
        self.db.execute(
            "UPDATE runq_task SET metahash=? WHERE task=?",
            (metahash, task))
        return


    def get_runq_task_metahash(self, task):
        task = self.task_id(task)
        return flatten_single_value(self.db.execute(
            "SELECT metahash FROM runq_task WHERE task=?", (task,)))


    def get_runq_buildhash(self, task):
        task = self.task_id(task)
        return flatten_single_value(self.db.execute(
                "SELECT buildhash FROM runq_task WHERE task=?", (task,)))


    def get_runq_task_buildhash(self, task):
        task = self.task_id(task)
        return flatten_single_value(self.db.execute(
            "SELECT buildhash FROM runq_task WHERE task=?", (task,)))




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


def var_to_tuple(v):
    return (v,)

def tuple_to_var(t):
    return t[0]
