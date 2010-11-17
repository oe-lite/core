from oebakery import die, err, warn, info, debug
from oelite import *
import sys, os, copy

class OEliteRunQueue:


    def __init__(self, db, cookbook, config):
        self.db = db
        self.cookbook = cookbook
        self.config = config
        self.assume_provided = (self.config.getVar("ASSUME_PROVIDED", 1)
                                or "").split()
        self.runable = []
        return


    def add_something(self, something, task_name):
        task_name = self.db.task_name_id(task_name)
        return (self.add_rprovider(something, task_name) or
                self.add_provider(something, task_name) or
                self.add_recipe(something, task_name) or
                self.add_package(something, task_name))


    def add_provider(self, item, task_name):
        package = self.get_provider(item, allow_no_provider=True)
        if not package:
            return False
        return self._add_package(package, task_name)


    def add_rprovider(self, ritem, task_name):
        package = self.get_rprovider(ritem, allow_no_provider=True)
        if not package:
            return False
        return self._add_package(package, task_name)


    def add_recipe(self, name, task_name):
        recipe = self.db.get_recipe_id(name)
        if not recipe:
            return False
        return self._add_recipe(recipe, task_name)


    def add_package(self, name, task_name):
        package = self.db.get_package_id(name)
        return self._add_package(package, task_name)


    def _add_package(self, package_id, task_name):
        if not package_id:
            return False
        return self._add_recipe(
            self.db.get_recipe_id(package=package_id), task_name)


    def _add_recipe(self, recipe_id, task_name):
        task = self.db.get_task_id(recipe_id, task_name)
        if not task:
            raise NoSuchTask("recipe %s do not have a %s task"%(
                    self.db.get_recipe(recipe_id),
                    self.db.get_task(task_name)))

        alltasks = set()
        addedtasks = set([task])

        while addedtasks:
            self.db.add_runq_tasks(addedtasks)
            alltasks.update(addedtasks)
            newtasks = set()
            for task in addedtasks:
                try:
                    newtasks.update(self.task_dependencies(task))
                except RecursiveDepends, e:
                    recipe = self.db.get_recipe({"task":task})
                    task = self.db.get_task(task=task)
                    raise RecursiveDepends(e.args[0], "%s:%s"%(recipe, task))

            addedtasks = newtasks.difference(alltasks)

        return True


    def task_dependencies(self, task):
        recipe_id = self.db.get_recipe_id(task=task)

        # add recipe-internal task parents
        # (ie. addtask X before Y after Z)
        parents = self.db.get_task_parents(task) or []
        tasks = set(parents)

        # helper to add multipe tasks of multipe recipes
        def add_tasks(task_names, recipes):
            for task_name in task_names:
                for recipe in recipes:
                    task = self.db.get_task_id(recipe, task_name)
                    if task:
                        tasks.add(task)
                    else:
                        debug("not adding unsupported task %s:%s"%(
                                recipe, task_name))

        # add deptask dependencies
        # (ie. do_sometask[deptask] = "do_someothertask")
        deptasks = self.db.get_task_deptasks(task)
        if deptasks:
            # get distinct list of recipes providing ${DEPENDS}
            (recipes, packages) = self.get_depends(recipe_id)
            # add each deptask of each recipe
            add_task(deptasks, recipes)

        # add rdeptask dependencies
        # (ie. do_sometask[rdeptask] = "do_someothertask")
        rdeptasks = self.db.get_task_rdeptasks(task)
        if rdeptasks:
            # get distinct list of recipes providing ${RDEPENDS}
            (recipes, packages) = self.get_rdepends(recipe_id)
            # add each rdeptask of each recipe
            add_tasks(rdeptasks, recipes)

        # add recdeptask dependencies
        # (ie. do_sometask[recdeptask] = "do_someothertask")
        recdeptasks = self.db.get_task_recdeptasks(task)
        if recdeptasks:
            # get cumulative and distinct list of recipes providing
            # ${DEPENDS} and recursively the corresponding
            # ${PACKAGE_DEPENDS_*}
            (recipes, packages) = self.get_depends(recipe_id, recursive=True)
            # add each recdeptask of each recipe
            add_tasks(recdeptasks, recipes)

        # add recrdeptask dependencies
        # (ie. do_sometask[recrdeptask] = "do_someothertask")
        recrdeptasks = self.db.get_task_recrdeptasks(task)
        if recrdeptasks:
            # get cumulative and distinct list of recipes providing
            # ${DEPENDS} and recursively the corresponding
            # ${PACKAGE_DEPENDS_*}
            (recipes, packages) = self.get_rdepends(recipe_id, recursive=True)
            # add each recdeptask of each recipe
            add_tasks(recrdeptasks, recipes)

        # add inter-task dependencies
        # (ie. do_sometask[depends] = "itemname:do_someothertask")
        taskdepends = self.db.get_task_depends(task) or []
        for taskdepend in taskdepends:
            if self.db.get_item(taskdepend[0]) in self.assume_provided:
                #debug("ASSUME_PROVIDED %s"%(
                #        self.db.get_item(taskdepend[0])))
                continue
            (recipe, package) = self.get_recipe_provider(taskdepend[0])
            if not recipe:
                raise NoProvider(taskdepend[0])
            add_tasks([taskdepend[1]], [recipe])

        # can self references occur?
        if task in tasks:
            die("self reference for task %s %s"%(
                    task, self.db.get_task(task=task)))

        # we are _not_ checking for multiple providers of the same
        # thing, as it is considered (in theory) to be a valid
        # use-case

        # add task dependency information to runq db
        self.db.add_runq_taskdepends(task, tasks)

        return tasks


    def get_depends(self, recipe, recursive=False):
        # this should not return items in ${ASSUME_PROVIDED}
        return self._get_depends(recipe, recursive,
                                 self.get_recipe_provider,
                                 self.db.get_item,
                                 self.db.get_package_depends,
                                 self.db.get_recipe_depends,
                                 self.db.set_runq_recdepends,
                                 self.db.get_runq_recdepends)


    def get_rdepends(self, recipe, recursive=False):
        return self._get_depends(recipe, recursive,
                                 self.get_recipe_rprovider,
                                 self.db.get_ritem,
                                 self.db.get_package_rdepends,
                                 self.db.get_recipe_rdepends,
                                 self.db.set_runq_recrdepends,
                                 self.db.get_runq_recrdepends)


    def _get_depends(self, recipe, recursive,
                     self_get_recipe_provider,
                     self_db_get_item,
                     self_db_get_package_depends,
                     self_db_get_recipe_depends,
                     self_db_set_runq_recdepends,
                     self_db_get_runq_recdepends):
        recipe = self.db.recipe_id(recipe)

        def simple_resolve(item, recursion_path):
            item_name = self_db_get_item(item)
            if item_name in self.assume_provided:
                #debug("ASSUME_PROVIDED %s"%(item_name))
                return ([], [])
            (recipe, package) = self_get_recipe_provider(item)
            return ([recipe], [package])

        def recursive_resolve(item, recursion_path):
            item_name = self_db_get_item(item)
            if item_name in self.assume_provided:
                #debug("ASSUME_PROVIDED %s"%(item_name))
                return ([], [])
            (recipe, package) = self_get_recipe_provider(item)

            # detect circular package dependencies
            if package in recursion_path[0]:
                debug("circular dependency while resolving %s"%(item_name))
                recipe_name = self.db.get_recipe(recipe)
                package_name = self.db.get_package(package)[0]

                depends = []
                recursion_path[0].append(package)
                recursion_path[1].append(item)
                for i in xrange(len(recursion_path[0])):
                    depend_package = self.db.get_package(
                        recursion_path[0][i])[0]
                    depend_item = self.db.get_item(recursion_path[1][i])
                    if depend_item == depend_package:
                        depends.append(depend_package)
                    else:
                        depends.append("%s:%s"%(depend_package, depend_item))
                raise RecursiveDepends(depends)

            # FIXME: detect circular recipe dependencies. remember to
            # handle inter-package recipe dependencies, ie. allow
            # recipe in recursion_path if it is the last recipe in the
            # path

            recursion_path[0].append(package)
            recursion_path[1].append(item)

            # cache recdepends tuple of list: (recipes, packages)
            recdepends = self_db_get_runq_recdepends(package)
            if recdepends:
                recdepends[0].append(recipe)
                recdepends[1].append(package)
                return recdepends

            recipes = set()
            packages = set()

            depends = self_db_get_package_depends(package)
            if depends:
                depender = self.db.get_package(package)[0]
                dependee = []
                for d in depends:
                    dependee.append(self_db_get_item(d))
                debug("db_get_package_depends: %s depends on %s"%(depender, dependee))
            if depends:
                for depend in depends:
                    _recursion_path = copy.deepcopy(recursion_path)
                    recdepends = recursive_resolve(depend, _recursion_path)
                    if recdepends[0]:
                        recipes.update(recdepends[0])
                    if recdepends[1]:
                        packages.update(recdepends[1])

            self_db_set_runq_recdepends(package, recipes, packages)

            recipes.add(recipe)
            packages.add(package)

            return (recipes, packages)

        if recursive:
            resolve = recursive_resolve
        else:
            resolve = simple_resolve
        
        depends = self_db_get_recipe_depends(recipe) or []

        recipes = set()
        packages = set()

        for depend in depends:
            recdepends = resolve(depend, ([], []))
            if recdepends[0]:
                recipes.update(recdepends[0])
            if recdepends[1]:
                packages.update(recdepends[1])

        return (recipes, packages)


    def get_recipe_provider(self, item):
        return self._get_recipe_provider(self.get_provider(item))


    def get_recipe_rprovider(self, item):
        return self._get_recipe_provider(self.get_rprovider(item))


    def _get_recipe_provider(self, package):
        if not package:
            raise NoProvider(item)
        recipe = self.db.get_recipe_id(package=package)
        return (recipe, package)


    def get_provider(self, item, allow_no_provider=False):
        return self._get_provider(item, allow_no_provider,
                                  self.db.item_id,
                                  self.db.get_item,
                                  self.db.get_runq_provider,
                                  self.db.set_runq_provider,
                                  self.db.get_providers,
                                  "PREFERRED_PROVIDER_")


    def get_rprovider(self, ritem, allow_no_provider=False):
        return self._get_provider(ritem, allow_no_provider,
                                  self.db.ritem_id,
                                  self.db.get_ritem,
                                  self.db.get_runq_rprovider,
                                  self.db.set_runq_rprovider,
                                  self.db.get_rproviders,
                                  "PREFERRED_RPROVIDER_")


    def _get_provider(self, item, allow_no_provider,
                     self_db_item_id,
                     self_db_get_item,
                     self_db_get_runq_provider,
                     self_db_set_runq_provider,
                     self_db_get_providers,
                     PREFERRED_PROVIDER_):

        if isinstance(item, str):
            item_id = self_db_item_id(item)
        elif isinstance(item, int):
            item_id = item
            item = self_db_get_item(item_id)

        provider = self_db_get_runq_provider(item)
        if provider:
            return provider

        def choose_provider(providers):
            import bb.utils

            # filter out all but the highest priority providers
            highest_preference = providers[0][2]
            for i in range(1, len(providers)):
                if providers[i][2] != highest_preference:
                    del providers[i:]
                    break
            if len(providers) == 1:
                self_db_set_runq_provider(item, providers[0][0])
                return providers[0][0]

            # filter out all but latest versions
            latest = {}
            for i in range(len(providers)):
                if not providers[i][1] in latest:
                    latest[providers[i][1]] = [ providers[i] ]
                    continue
                vercmp = bb.utils.vercmp_part(
                    latest[providers[i][1]][0][2], providers[i][2])
                if vercmp < 0:
                    latest = [ providers[i] ]
                elif vercmp == 0:
                    latest[providers[i][1]].append(providers[i])
            if len(latest) == 1:
                package = latest.values()[0][0][0]
                recipe = self.db.recipe_id({"package": package})
                self_db_set_runq_provider(item, recipe)
                return latest.values()[0][0][0]
            if len(latest) > 1:
                multiple_providers = []
                for provider in latest.itervalues():
                    multiple_providers.append(provider[1])
                raise MultipleProviders(
                    "multiple providers: " + " ".join(multiple_providers))
            raise Exception("code path should never go here...")

        # first try with preferred provider and version
        # then try with prerred provider
        # and last any provider
        preferred_provider = self.config.getVar(
            PREFERRED_PROVIDER_ + item, 1) or None
        if preferred_provider:
            preferred_version = self.config.getVar(
                "PREFERRED_VERSION_" + preferred_provider, 1) or None
            if preferred_version:
                providers = self_db_get_providers(
                    item, prefferred_provider, preferred_version)
                if len(providers) == 1:
                    self_db_set_runq_provider(item, providers[0][0])
                    return providers[0][0]
                elif len(providers) > 1:
                    return choose_provider(providers)
            providers = self_db_get_providers(item, preferred_provider)
            if len(providers) == 1:
                self_db_set_runq_provider(item, providers[0][0])
                return providers[0][0]
            elif len(providers) > 1:
                return choose_provider(providers)
        providers = self_db_get_providers(item)
        if len(providers) == 1:
            self_db_set_runq_provider(item, providers[0][0])
            return providers[0][0]
        elif len(providers) > 1:
            return choose_provider(providers)
        if allow_no_provider:
            return None
        raise NoProvider(item)


    def update_tasks(self):

        # start from leaf dependencies, and then next level and so on,
        # and for each dependency determine if it needs to be rebuild,
        # based on recipe checksum, src checksum, and dependency
        # checksum.  when a dependency has a different checksum, all
        # tasks that depend on it (recursively) will also have
        # different checksum because of the dependency checksum and
        # will therefore have to be rebuilt

        # on each iteration on the above, the dependency tree must be
        # updated so the next iteration can find the next dependencies
        # to check.  maintain (in a relation in db) a list of
        # still-not-checked dependency checksums. at the end of each
        # iteration, the just computed dependency checksums is deleted
        # from this list, and a select query can then find the tasks
        # that now have 0 missing dependency checksums and have not
        # been checked yet (which should be kept in a "boolean" db
        # relation)

        tasks = self.db.get_runq_leaftasks()
        #"SELECT task FROM runq_taskdepend WHERE depend IS NULL"

        while tasks:
            for task in tasks:
                self.update_task(task)
            tasks = self.db.get_runq_hashabletasks()
            # "SELECT task FROM runq_taskdepends WHERE hashed_depends=total_depends"

        # check if there are still tasks that are not hashed.  if this
        # is the case, the metadata is broken (ie. circular
        # dependencies), and this function should return False and
        # developer should debug/fix the metadata

        return


    def update_task(self, task):

        get_recipe_datahash(task.recipe)
        if task is fetch:
            get_recipe_srchash(task.recipe)
        get_dependencies_hash(task)
        taskhash = hashit(recipehash, srchash, dephash)
        run=0
        if has_build(task):
            if datahash != build_datahash(task):
                info("recipe changes trigger run")
                run=1
            if srchash != build_srchash(task):
                info("src changes trigger run")
                run=1
            if dephash != build_dephash(task):
                info("dep changes trigger run")
                run=1
        else:
            info("no existing build")
            run=1
        if run:
            set_runable(task, datahash, srchash, dephash)
            # this marks task for run
            # and saves a combined taskhash for following
            # iterations (into runq_taskdepend.hash)
            # and all hashes for saving with build
            # result
            set_runq_taskdepend_checked(task)

        return


    def get_runabletask(self):
        newrunable = self.db.get_runabletasks()
        if newrunable:
            self.runable = newrunable + self.runable
            for task in newrunable:
                self.db.set_runq_task_running(task)
        if not self.runable:
            return None
        task = self.runable.pop()
        return task


    def mark_done(self, task):
        return self.db.set_runq_task_done(task)
