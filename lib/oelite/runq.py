from oebakery import die, err, warn, info, debug
from oelite import *
import sys, os, copy

class OEliteRunQueue:


    def __init__(self, db, cookbook, config, rebuild=None, relax=None,
                 depth_first=True):
        self.db = db
        self.cookbook = cookbook
        self.config = config
        # 1: --rebuild, 2: --rebuildall, 3: --reallyrebuildall
        self.rebuild = rebuild
        self.relax = relax
        self.depth_first = depth_first
        self._assume_provided = (self.config.getVar("ASSUME_PROVIDED", 1)
                                or "").split()
        self.runable = []
        self.metahashable = []
        return


    def assume_provided(self, item):
        if isinstance(item, str) or isinstance(item, unicode):
            return item in self._assume_provided
        return self.db.get_item(item) in self._assume_provided


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
        recipe = self.db.get_recipe_id(name=name)
        if not recipe:
            return False
        return self._add_recipe(recipe, task_name, primary=True)


    def add_package(self, name, task_name):
        package = self.db.get_package_id(name=name)
        return self._add_package(package, task_name)


    def _add_package(self, package_id, task_name):
        if not package_id:
            return False
        return self._add_recipe(
            self.db.get_recipe_id(package=package_id), task_name, primary=True)


    def _add_recipe(self, recipe_id, task_name, primary=False):
        if primary:
            primary_recipe_id = recipe_id
        else:
            primary_recipe_id = None
        primary_task = self.db.get_task_id(recipe_id, task_name)
        if not primary_task:
            raise NoSuchTask("%s:%s"%(
                    self.db.get_recipe_name(recipe_id),
                    self.db.get_task(task_name)))

        alltasks = set()
        addedtasks = set([primary_task])

        while addedtasks:
            self.db.add_runq_tasks(addedtasks)

            alltasks.update(addedtasks)
            newtasks = set()
            for task in addedtasks:

                recipe_id = self.db.recipe_id({"task": task})
                recipe_data = self.cookbook[recipe_id].data

                if recipe_id == primary_recipe_id:
                    is_primary_recipe = True
                else:
                    is_primary_recipe = False

                # set rebuild flag (based on
                # --rebuild/--rebuildall/--reallyrebuildall)
                if ((self.rebuild >= 1 and is_primary_recipe) or
                    (self.rebuild == 2 and
                     recipe_data.getVar("REBUILDALL_SKIP", True) != "1") or
                    (self.rebuild == 3)):
                    self.db.set_runq_task_build(task)

                # set relax flag (based on --sloppy/--relaxed)
                if ((self.relax == 2 and not is_primary_recipe) or
                    (self.relax == 1 and
                     (not is_primary_recipe and
                      recipe_data.getVar("RELAXED", True)))):
                    self.db.set_runq_task_relax(task)

                try:
                    # task_dependencies should return tuple:
                    # task_depends: list of task_id's
                    # package_depends: list of (task_id, package_id)
                    # package_rdepends: list of (task_id, package_id)
                    (task_depends, package_depends, package_rdepends) = \
                        self.task_dependencies(task)
                    self.db.add_runq_task_depends(task, task_depends)
                    self.db.add_runq_package_depends(task, package_depends)
                    self.db.add_runq_package_rdepends(task, package_rdepends)
                    newtasks.update(task_depends)
                    newtasks.update([d[0] for d in package_depends])
                    newtasks.update([d[0] for d in package_rdepends])
                except RecursiveDepends, e:
                    recipe = self.db.get_recipe_name({"task":task})
                    task = self.db.get_task(task=task)
                    raise RecursiveDepends(e.args[0], "%s:%s"%(recipe, task))

            addedtasks = newtasks.difference(alltasks)

        self.db.set_runq_task_primary(primary_task)
        return True


    def task_dependencies(self, task):
        recipe_id = self.db.get_recipe_id(task=task)

        # add recipe-internal task parents
        # (ie. addtask X before Y after Z)
        parents = self.db.get_task_parents(task) or []
        task_depends = set(parents)

        package_depends = set()
        package_rdepends = set()

        # helper to add multipe task_depends
        def add_task_depends(task_names, recipes):
            for task_name in task_names:
                for recipe in recipes:
                    task = self.db.get_task_id(recipe, task_name)
                    if task:
                        task_depends.add(task)
                    else:
                        debug("not adding unsupported task %s:%s"%(
                                recipe, task_name))

        # helpers to add multipe package_depends / package_rdepends
        def add_package_depends(task_names, depends):
            return _add_package_depends(task_names, depends, package_depends)

        def add_package_rdepends(task_names, rdepends):
            return _add_package_depends(task_names, rdepends, package_rdepends)

        def _add_package_depends(task_names, depends, package_depends):
            for task_name in task_names:
                for (recipe, package) in depends:
                    task = self.db.get_task_id(recipe, task_name)
                    if task:
                        package_depends.add((task, package))
                    else:
                        debug("not adding unsupported task %s:%s"%(
                                recipe, task_name))

        # add deptask dependencies
        # (ie. do_sometask[deptask] = "do_someothertask")
        deptasks = self.db.get_task_deptasks(task)
        if deptasks:
            # get list of (recipe, package) providing ${DEPENDS}
            depends = self.get_depends(recipe_id)
            # add each deptask for each (recipe, package)
            add_package_depends(deptasks, depends)

        # add rdeptask dependencies
        # (ie. do_sometask[rdeptask] = "do_someothertask")
        rdeptasks = self.db.get_task_rdeptasks(task)
        if rdeptasks:
            # get list of (recipe, package) providing ${RDEPENDS}
            rdepends = self.get_rdepends(recipe_id)
            # add each rdeptask for each (recipe, package)
            add_package_rdepends(rdeptasks, rdepends)

        # add recursive (build) depends tasks
        # (ie. do_sometask[recdeptask] = "do_someothertask")
        recdeptasks = self.db.get_task_recdeptasks(task)
        if recdeptasks:
            # get cumulative list of (recipe, package) providing
            # ${DEPENDS} and recursively the corresponding
            # ${PACKAGE_DEPENDS_*}
            depends = self.get_depends(recipe_id, recursive=True)
            # add each recdeptask for each (recipe, package)
            add_package_depends(recdeptasks, depends)

        # add recursive run-time depends tasks
        # (ie. do_sometask[recrdeptask] = "do_someothertask")
        recrdeptasks = self.db.get_task_recrdeptasks(task)
        if recrdeptasks:
            # get cumulative list of (recipe, package) providing
            # ${RDEPENDS} and recursively the corresponding
            # ${PACKAGE_RDEPENDS_*}
            rdepends = self.get_rdepends(recipe_id, recursive=True)
            # add each recdeptask of each (recipe, package)
            add_package_rdepends(recrdeptasks, rdepends)

        # add recursive all depends tasks
        # (ie. do_sometask[recadeptask] = "do_someothertask")
        recadeptasks = self.db.get_task_recadeptasks(task)
        if recadeptasks:
            # get all inclusive cumulative list of (recipe, package)
            # involved in a full build, including recursively all
            # ${DEPENDS}, ${RDEPENDS}, ${PACKAGE_DEPENDS_*} and
            # ${PACKAGE_RDEPENDS_*}
            depends = self.get_adepends(recipe_id, recursive=True)
            # get distinct recipe list
            depends = dict(depends).keys()
            # add each recdeptask for each (recipe, package)
            add_task_depends(recadeptasks, depends)

        # add inter-task dependencies
        # (ie. do_sometask[depends] = "itemname:do_someothertask")
        taskdepends = self.db.get_task_depends(task) or []
        for taskdepend in taskdepends:
            task_name = self.db.get_task(task=task)
            recipe_name = self.db.get_recipe_name(recipe_id)
            raise Exception("OE-lite does not support inter-task dependencies! %s:%s"%(recipe_name, task_name))
            if self.assume_provided(taskdepend[0]):
                #debug("ASSUME_PROVIDED %s"%(
                #        self.db.get_item(taskdepend[0])))
                continue
            (recipe, package) = self.get_recipe_provider(taskdepend[0])
            if not recipe:
                raise NoProvider(taskdepend[0])
            add_task_depends([taskdepend[1]], [recipe])

        # can self references occur?
        #if task in tasks:
        #    die("self reference for task %s %s"%(
        #            task, self.db.get_task(task=task)))

        # we are _not_ checking for multiple providers of the same
        # thing, as it is considered (in theory) to be a valid
        # use-case

        # add task dependency information to runq db
        self.db.add_runq_task_depends(task, task_depends)
        self.db.add_runq_package_depends(task, package_depends)
        self.db.add_runq_package_rdepends(task, package_rdepends)

        return (task_depends, package_depends, package_rdepends)


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
            if self.assume_provided(item_name):
                #debug("ASSUME_PROVIDED %s"%(item_name))
                return ([], [])
            (recipe, package) = self_get_recipe_provider(item)
            return ([recipe], [package])

        def recursive_resolve(item, recursion_path):
            item_name = self_db_get_item(item)
            if self.assume_provided(item_name):
                #debug("ASSUME_PROVIDED %s"%(item_name))
                return set([])
            (recipe, package) = self_get_recipe_provider(item)

            # detect circular package dependencies
            if package in recursion_path[0]:
                # actually, this might not be a bug/problem.......
                # Fx: package X rdepends on package Y, and package Y
                # rdepends on package X. As long as X and Y can be
                # built, anyone rdepend'ing on either X or Y will just
                # get both.  Bad circular dependencies must be
                # detected at runq task level.  If we cannot build a
                # recipe because of circular task dependencies, it is
                # clearly a bug.  Improve runq detection of this by
                # always simulating runq execution before starting,
                # and checking that all tasks can be completed, and if
                # some tasks are unbuildable, print out remaining
                # tasks and their dependencies.

                # on the other hand.... circular dependencies can be
                # arbitrarely complex, and it is pretty hard to handle
                # them generally, so better refuse to handle any of
                # them, to avoid having to add more and more complex
                # code to handle growingly sophisticated types of
                # circular dependencies.

                err("circular dependency while resolving %s"%(item_name))
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

            # Recipe/task based circular dependencies are detected
            # later on when the entire runq has been constructed

            recursion_path[0].append(package)
            recursion_path[1].append(item)

            # cache recdepends list of (recipe, package)
            recdepends = self_db_get_runq_recdepends(package)
            if recdepends:
                recdepends.append((recipe, package))
                return recdepends

            recdepends = set()

            depends = self_db_get_package_depends(package)
            if depends:
                for depend in depends:
                    _recursion_path = copy.deepcopy(recursion_path)
                    _recdepends = recursive_resolve(depend, _recursion_path)
                    recdepends.update(_recdepends)

            self_db_set_runq_recdepends(package, recdepends)

            recdepends.update([(recipe, package)])
            return recdepends

        if recursive:
            resolve = recursive_resolve
        else:
            resolve = simple_resolve

        depends = self_db_get_recipe_depends(recipe) or []

        recdepends = set()

        for depend in depends:
            _recdepends = resolve(depend, ([], []))
            recdepends.update(_recdepends)

        return recdepends


    def get_adepends(self, recipe, recursive=True):
        return set()


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
        try:
            return self._get_provider(item, allow_no_provider,
                                      self.db.item_id,
                                      self.db.get_item,
                                      self.db.get_runq_provider,
                                      self.db.set_runq_provider,
                                      self.db.get_providers,
                                      "PREFERRED_PROVIDER_")
        except MultipleProviders, e:
            die("multiple providers for %s: %s"%(
                    self.db.get_item(item), e))


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
            highest_preference = providers[0][3]
            for i in range(1, len(providers)):
                if providers[i][3] != highest_preference:
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
                    latest[providers[i][1]] = [ providers[i] ]
                elif vercmp == 0:
                    latest[providers[i][1]].append(providers[i])
            if len(latest) == 1:
                package = latest.values()[0][0][0]
                recipe = self.db.recipe_id({"package": package})
                self_db_set_runq_provider(item, package)
                return latest.values()[0][0][0]
            if len(latest) > 1:
                multiple_providers = []
                for provider in latest.itervalues():
                    multiple_providers.append(provider[0][1])
                raise MultipleProviders(
                    "multiple providers: " + " ".join(multiple_providers))
            raise Exception("code path should never go here...")

        # first try with preferred provider and version
        # then try with prerred provider
        # and last any provider

        # in self.config, the variable names have not been extended yet...
        preferred_provider = PREFERRED_PROVIDER_ + item
        sdk_arch = self.config.getVar("SDK_ARCH", True)
        if item.startswith(sdk_arch + "/"):
            preferred_provider = PREFERRED_PROVIDER_ + item.replace(sdk_arch, "${SDK_ARCH}", 1)
        machine_arch = self.config.getVar("MACHINE_ARCH", True)
        if item.startswith(machine_arch + "/"):
            preferred_provider = PREFERRED_PROVIDER_ + item.replace(machine_arch, "${MACHINE_ARCH}", 1)
        build_arch = self.config.getVar("BUILD_ARCH", True)
        if item.startswith(build_arch + "/"):
            preferred_provider = PREFERRED_PROVIDER_ + item.replace(build_arch, "${BUILD_ARCH}", 1)
        preferred_provider = self.config.getVar(preferred_provider, True) or None

        if preferred_provider:
            preferred_version = self.config.getVar(
                "PREFERRED_VERSION_" + preferred_provider, 1) or None
            if preferred_version:
                providers = self_db_get_providers(
                    item, preferred_provider, preferred_version)
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
        newrunable = self.db.get_readytasks()
        if newrunable:
            if self.depth_first:
                self.runable += newrunable
            else:
                self.runable = newrunable + self.runable
            for task in newrunable:
                self.db.set_runq_task_pending(task)
        if not self.runable:
            return None
        task = self.runable.pop()
        return task


    def get_metahashable_task(self):
        if not self.metahashable:
            self.metahashable = list(self.db.get_metahashable_tasks())
        if not self.metahashable:
            return None
        return self.metahashable.pop()


    def mark_done(self, task, delete=True):
        return self.db.set_runq_task_done(task, delete)
