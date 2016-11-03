import oebakery
from oebakery import die, err, warn, info, debug
from oelite import *
from recipe import OEliteRecipe
from runq import OEliteRunQueue
from priq import PriorityQueue
from oven import OEliteOven
import oelite.meta
import oelite.util
import oelite.arch
import oelite.parse
import oelite.task
import oelite.item
from oelite.parse import *
from oelite.cookbook import CookBook
import oelite.profiling

import oelite.fetch

import bb.utils

import sys
import os
import glob
import shutil
import hashlib
import logging

#INITIAL_OE_IMPORTS = "oe.path oe.utils sys os time"
INITIAL_OE_IMPORTS = "sys os time"

def add_bake_parser_options(parser):
    parser.add_option("-t", "--task",
                      action="store", type="str", default=None,
                      help="task(s) to do")

    parser.add_option("--rebuild",
                      action="append_const", dest="rebuild", const=1,
                      help="rebuild specified recipes")
    parser.add_option("--rebuildall",
                      action="append_const", dest="rebuild", const=2,
                      help="rebuild specified recipes and all dependencies (except cross and native)")
    parser.add_option("--reallyrebuildall",
                      action="append_const", dest="rebuild", const=3,
                      help="rebuild specified recipes and all dependencies")

    parser.add_option("--relaxed",
                      action="append_const", dest="relax", const=1,
                      help="don't rebuild ${RELAXED} recipes because of metadata changes")
    parser.add_option("--sloppy",
                      action="append_const", dest="relax", const=2,
                      help="don't rebuild dependencies because of metadata changes")

    parser.add_option("-y", "--yes",
                      action="store_true", default=False,
                      help="assume 'y' response to trivial questions")

    parser.add_option("--rmwork",
                      action="store_true", default=None,
                      help="clean workdir for all recipes being built")
    parser.add_option("--no-rmwork",
                      action="store_false", dest="rmwork", default=None,
                      help="do not clean workdir for all recipes being built")

    parser.add_option("--no-prebake",
                      action="store_false", dest="prebake", default=True,
                      help="do not use prebaked packages")

    parser.add_option("--dump-signature-metadata",
                      action="store", type="str", default=None, metavar="DIR",
                      help="dump task metadata used for calculating task signatures to DIR")

    parser.add_option("--fake-build",
                      action="store_true", default=False,
                      help="don't actually run the tasks, but record state as if they were")

    return


def add_show_parser_options(parser):
    parser.add_option("--nohash",
                      action="store_true",
                      help="don't show variables that will be ignored when computing data hash")
    parser.add_option("-t", "--task",
                      action="store", type="str", default=None,
                      metavar="TASK",
                      help="prepare recipe for TASK before showing")

    return


class OEliteBaker:

    @oelite.profiling.profile_rusage_delta
    def __init__(self, options, args, config):
        self.options = options
        self.debug = self.options.debug
        self.debug_loglines = getattr(self.options, 'debug_loglines', None)

        # Bakery 3 compatibility, configure the logging module
        if (not hasattr(oebakery, "__version__") or
            oebakery.__version__.split(".")[0] < 4):
            logging.basicConfig(format="%(message)s")
            if self.debug:
                logging.getLogger().setLevel(logging.DEBUG)
            else:
                logging.getLogger().setLevel(logging.INFO)

        self.config = oelite.meta.DictMeta(meta=config)
        self.config["OE_IMPORTS"] = INITIAL_OE_IMPORTS
        self.config.import_env()
        os.environ.clear()
        self.config.pythonfunc_init()
        self.topdir = self.config.get("TOPDIR", True)
        self.set_manifest_origin()
        # FIXME: self.config.freeze("TOPDIR")

        self.confparser = confparse.ConfParser(self.config)
        self.confparser.parse("conf/oe-lite.conf")

        oelite.pyexec.exechooks(self.config, "post_conf_parse")

        # FIXME: refactor oelite.arch.init to a post_conf_parse hook
        oelite.arch.init(self.config)

        # Handle any INHERITs and inherit the base class
        inherits  = ["core"] + (self.config.get("INHERIT", 1) or "").split()
        # and inherit rmwork when needed
        try:
            rmwork = self.options.rmwork
            if rmwork is None:
                rmwork = self.config.get("RMWORK", True)
                if rmwork == "0":
                    rmwork = False
            if rmwork:
                debug("rmwork")
                inherits.append("rmwork")
                self.options.rmwork = True
        except AttributeError:
            pass
        self.oeparser = oeparse.OEParser(self.config)
        for inherit in inherits:
            self.oeparser.reset_lexstate()
            self.oeparser.parse("classes/%s.oeclass"%(inherit), require=True)

        oelite.pyexec.exechooks(self.config, "post_common_inherits")

        self.cookbook = CookBook(self)

        # things (ritem, item, recipe, or package) to do
        if args:
            self.things_todo = args
        elif "OE_DEFAULT_THING" in self.config:
            self.things_todo = self.config.get("OE_DEFAULT_THING", 1).split()
        else:
            self.things_todo = [ "world" ]

        recipe_types = ("machine", "native", "sdk",
                        "cross", "sdk-cross", "canadian-cross")
        def thing_todo(thing):
            if not thing in self.things_todo:
                self.things_todo.append(thing)
        def dont_do_thing(thing):
            while thing in self.things_todo:
                self.things_todo.remove(thing)
        self.recipes_todo = set()
        if "universe" in self.things_todo:
            dont_do_thing("universe")
            for recipe_type in recipe_types:
                thing_todo(recipe_type + ":world")
        if "world" in self.things_todo:
            dont_do_thing("world")
            thing_todo("machine:world")
        for recipe_type in recipe_types:
            world = recipe_type + ":world"
            if world in self.things_todo:
                dont_do_thing(world)
                for recipe in self.cookbook.get_recipes(type=recipe_type):
                    self.recipes_todo.add(recipe)

        return


    def __del__(self):
        return


    def set_manifest_origin(self):
        if not os.path.exists(os.path.join(self.topdir, '.git')):
            return
        url = oelite.util.shcmd("git config --get remote.origin.url",
                                quiet=True, silent_errorcodes=[1])
        if not url:
            return
        url = os.path.dirname(url.strip())
        if url.startswith('file:///'):
            url = url[7:]
        srcuri = None
        protocols = ('git', 'ssh', 'http', 'https', 'ftp', 'ftps', 'rsync')
        if url.startswith('/'):
            srcuri = 'git://%s'%(url)
            protocol = 'file'
        elif url.startswith('git://'):
            srcuri = url
            protocol = None
        elif not url.split('://')[0] in protocols:
            url = 'ssh://' + url.replace(':', '/', 1)
        if srcuri is None:
            for protocol in protocols:
                if url.startswith('%s://'%(protocol)):
                    srcuri = 'git://%s'%(url[len(protocol)+3:])
                    break
        self.config.set('MANIFEST_ORIGIN_URL', url)
        self.config.set_flag('MANIFEST_ORIGIN_URL', 'nohash', True)
        if srcuri is None:
            logging.warning("unsupported manifest origin: %s"%(url))
            return
        self.config.set('MANIFEST_ORIGIN_SRCURI', srcuri)
        self.config.set_flag('MANIFEST_ORIGIN_SRCURI', 'nohash', True)
        if protocol:
            self.config.set('MANIFEST_ORIGIN_PARAMS', ';protocol=%s'%(protocol))
        else:
            self.config.set('MANIFEST_ORIGIN_PARAMS', '')
        self.config.set_flag('MANIFEST_ORIGIN_PARAMS', 'nohash', True)


    def show(self):

        if len(self.things_todo) == 0:
            die("you must specify something to show")
        if len(self.recipes_todo) > 0:
            die("you cannot show world")

        thing = oelite.item.OEliteItem(self.things_todo[0])
        recipe = self.cookbook.get_recipe(
            type=thing.type, name=thing.name, version=thing.version,
            strict=False)
        if not recipe:
            die("Cannot find %s"%(thing))

        if self.options.task:
            if self.options.task.startswith("do_"):
                task = self.options.task
            else:
                task = "do_" + self.options.task
            self.runq = OEliteRunQueue(self.config, self.cookbook)
            self.runq._add_recipe(recipe, task)
            task = self.cookbook.get_task(recipe=recipe, name=task)
            task.prepare()
            meta = task.meta()
        else:
            meta = recipe.meta

        #meta.dump(pretty=False, nohash=False, flags=True,
        #          ignore_flags=re.compile("filename|lineno"),
        meta.dump(pretty=True, nohash=(not self.options.nohash),
                  only=(self.things_todo[1:] or None))

        return 0


    def bake(self):

        self.setup_tmpdir()
        oelite.profiling.init(self.config)

        # task(s) to do
        if self.options.task:
            tasks_todo = self.options.task
        elif "OE_DEFAULT_TASK" in self.config:
            tasks_todo = self.config.get("OE_DEFAULT_TASK", 1)
        else:
            #tasks_todo = "all"
            tasks_todo = "build"
        self.tasks_todo = tasks_todo.split(",")

        if self.options.rebuild:
            self.options.rebuild = max(self.options.rebuild)
            self.options.prebake = False
        else:
            self.options.rebuild = None
        if self.options.relax:
            self.options.relax = max(self.options.relax)
        else:
            default_relax = self.config.get("DEFAULT_RELAX", 1)
            if default_relax and default_relax != "0":
                self.options.relax = int(default_relax)
            else:
                self.options.relax = None

        # init build quue
        self.runq = OEliteRunQueue(self.config, self.cookbook,
                                   self.options.rebuild, self.options.relax)

        # first, add complete dependency tree, with complete
        # task-to-task and task-to-package/task dependency information
        debug("Building dependency tree")
        rusage = oelite.profiling.Rusage("Building dependency tree")
        for task in self.tasks_todo:
            task = oelite.task.task_name(task)
            try:
                for thing in self.recipes_todo:
                    if not self.runq.add_recipe(thing, task):
                        die("No such recipe: %s"%(thing))
                for thing in self.things_todo:
                    thing = oelite.item.OEliteItem(thing)
                    if not self.runq.add_something(thing, task):
                        die("No such thing: %s"%(thing))
            except RecursiveDepends, e:
                die("dependency loop: %s\n\t--> %s"%(
                        e.args[1], "\n\t--> ".join(e.args[0])))
            except NoSuchTask, e:
                die("No such task: %s: %s"%(thing, e.__str__()))
            except oebakery.FatalError, e:
                die("Failed to add %s:%s to runqueue"%(thing, task))
        rusage.end()

        # Generate recipe dependency graph
        recipes = set([])
        for task in self.runq.get_tasks():
            task_deps = self.runq.task_dependencies(task, flatten=True)
            recipe = task.recipe
            recipe.add_task(task, task_deps)
            recipes.add(recipe)
        unresolved_recipes = []
        for recipe in recipes:
            unresolved_recipes.append((recipe, list(recipe.recipe_deps)))

        # Traverse recipe dependency graph, propagating EXTRA_ARCH on
        # recipe level.
        resolved_recipes = set([])
        while len(unresolved_recipes) > 0:
            progress = False
            for i in xrange(len(unresolved_recipes)-1, -1, -1):
                recipe, unresolved_deps = unresolved_recipes[i]
                resolved = True
                for j in xrange(len(unresolved_deps)-1, -1, -1):
                    recipe_dep = unresolved_deps[j]
                    if not recipe_dep in resolved_recipes:
                        continue
                    recipe_dep_extra_arch = recipe_dep.meta.get("EXTRA_ARCH")
                    if recipe_dep_extra_arch:
                        # FIXME: sanity check for inconsistent EXTRA_ARCH here
                        recipe.meta.set("EXTRA_ARCH", recipe_dep_extra_arch)
                    del unresolved_deps[j]
                if len(unresolved_deps) == 0:
                    resolved_recipes.add(recipe)
                    del unresolved_recipes[i]
                    progress = True
                    oelite.pyexec.exechooks(recipe.meta, "post_extra_arch")
            if not progress:
                foo = ""
                for r, deps in unresolved_recipes:
                    foo += "\n %s(%s)"%(r, ",".join(map(str, deps)))
                die("recipe EXTRA_ARCH resolving deadlocked!" + foo)

        # update runq task list, checking recipe and src hashes and
        # determining which tasks needs to be run
        # examing each task, computing it's hash, and checking if the
        # task has already been built, and with the same hash.
        task = self.runq.get_metahashable_task()
        total = self.runq.number_of_runq_tasks()
        count = 0
        rusage = oelite.profiling.Rusage("Calculating task metadata hashes")
        while task:
            oelite.util.progress_info("Calculating task metadata hashes",
                                      total, count)
            recipe = task.recipe

            if task.nostamp:
                self.runq.set_task_metahash(task, "0")
                task = self.runq.get_metahashable_task()
                count += 1
                continue

            dephashes = {}
            for depend in self.runq.task_dependencies(task, flatten=True):
                dephashes[depend] = self.runq.get_task_metahash(depend)
            try:
                recipe_extra_arch = recipe.meta.get("EXTRA_ARCH")
            except oelite.meta.ExpansionError as e:
                e.msg += " in %s"%(task)
                raise
            task_meta = task.meta()
            # FIXME: is this really needed?  How should the task metadata be
            # changed at this point?  isn't it created from recipe meta by the
            # task.meta() call above?
            if (recipe_extra_arch and
                task_meta.get("EXTRA_ARCH") != recipe_extra_arch):
                task_meta.set("EXTRA_ARCH", recipe_extra_arch)
            try:
                if self.options.dump_signature_metadata:
                    self.normpath(task.recipe.filename)
                    dump = os.path.join(self.options.dump_signature_metadata,
                                        self.normpath(task.recipe.filename),
                                        str(task))
                else:
                    dump = None
                datahash = task_meta.signature(dump=dump)
            except oelite.meta.ExpansionError as e:
                e.msg += " in %s"%(task)
                raise

            hasher = hashlib.md5()
            hasher.update(str(sorted(dephashes.values())))
            dephash = hasher.hexdigest()

            hasher = hashlib.md5()
            hasher.update(datahash)
            hasher.update(dephash)
            metahash = hasher.hexdigest()

            # FIXME: instad of all of the above
            # metasig = task.get_meta_signature()

            #if self.debug:
            #    recipe_name = self.db.get_recipe(recipe_id)
            #    task_name = self.db.get_task(task=task)
            #    debug(" %d %s:%s data=%s dep=%s meta=%s"%(
            #            task, "_".join(recipe_name), task_name,
            #            datahash, dephash, metahash))

            self.runq.set_task_metahash(task, metahash)

            (stamp_mtime, stamp_signature) = task.read_stamp()
            if not stamp_mtime:
                self.runq.set_task_build(task)
            else:
                self.runq.set_task_stamp(task, stamp_mtime, stamp_signature)

            task = self.runq.get_metahashable_task()
            count += 1
            continue

        oelite.util.progress_info("Calculating task metadata hashes",
                                  total, count)

        rusage.end()

        if count != total:
            print ""
            self.runq.print_metahashable_tasks()
            err("Circular task dependencies detected. Remaining tasks:")
            for task in self.runq.get_unhashed_tasks():
                print "  %s"%(task)
            die("Unable to handle circular task dependencies")

        self.runq.set_task_build_on_nostamp_tasks()
        self.runq.set_task_build_on_retired_tasks()
        self.runq.set_task_build_on_hashdiff()

        # check for availability of prebaked packages, and set package
        # filename for all packages.
        depend_packages = self.runq.get_depend_packages()
        url_prefix = self.config.get("PREBAKE_URL")
        if url_prefix is not None:
            info("Trying to use prebakes from url: %s"%(url_prefix))
        for package in depend_packages:
            recipe = self.cookbook.get_recipe(package=package)
            if recipe.get("REBUILD") == "1":
                continue
            prebake = self.find_prebaked_package(package)
            if prebake:
                self.runq.set_package_filename(package, prebake,
                                               prebake=True)

        # clear parent_task for all runq_depends where all runq_depend
        # rows with the same parent_task has prebake flag set
        self.runq.prune_prebaked_runq_depends()

        # FIXME: this might prune to much. If fx. A depends on B and
        # C, and B depends on C, and all A->B dependencies are
        # prebaked, but not all A->C dependencies, B will be used
        # prebaked, and A will build with a freshly built C, which
        # might be different from the C used in B.  This is especially
        # risky when manually fidling with content of WORKDIR manually
        # (fx. manually fixing something to get do_compile to
        # complete, and then wanting to test the result before
        # actually integrating it in the recipe).  Hmm....  Why not
        # just add a --no-prebake option, so when developer is
        # touching WORKDIR manually, this should be used to avoid
        # strange prebake issues.  The mtime / retired task stuff
        # should guarantee that consistency is kept then.

        # Argh! if prebake is to work with rmwork, we might have to do
        # the above after all :-( We will now have som self.runq_depends
        # with parent_task.prebake flag set, but when we follow its
        # dependencies, we will find one or more recipes that has to
        # be rebuilt, fx. because of a --rebuild flag.

        self.runq.propagate_runq_task_build()

        build_count = self.runq.set_buildhash_for_build_tasks()
        nobuild_count = self.runq.set_buildhash_for_nobuild_tasks()
        if (build_count + nobuild_count) != total:
            die("build_count + nobuild_count != total")

        deploy_dir = self.config.get("PACKAGE_DEPLOY_DIR", True)
        packages = self.runq.get_packages_to_build()
        for package in packages:
            package = self.cookbook.get_package(id=package)
            recipe = self.cookbook.get_recipe(package=package.id)
            buildhash = self.runq.get_package_buildhash(package.id)
            filename = os.path.join(
                deploy_dir, package.type,
                package.arch + (package.recipe.meta.get("EXTRA_ARCH") or ""),
                "%s_%s_%s.tar"%(package.name, recipe.version, buildhash))
            debug("will use from build: %s"%(filename))
            self.runq.set_package_filename(package.id, filename)

        self.runq.mark_primary_runq_depends()
        self.runq.prune_runq_depends_nobuild()
        self.runq.prune_runq_depends_with_nobody_depending_on_it()
        self.runq.prune_runq_tasks()

        remaining = self.runq.number_of_tasks_to_build()
        debug("%d tasks remains"%remaining)

        recipes = self.runq.get_recipes_with_tasks_to_build()
        if not recipes:
            info("Nothing to do")
            return 0

        if self.options.rmwork:
            for recipe in recipes:
                if (tasks_todo != ["build"]
                    and self.runq.is_recipe_primary(recipe[0])):
                    debug("skipping...")
                    continue
                debug("adding %s:do_rmwork"%(recipe[1]))
                recipe = self.cookbook.get_recipe(recipe[0])
                self.runq._add_recipe(recipe, "do_rmwork")
                task = self.cookbook.get_task(recipe=recipe, name="do_rmwork")
                self.runq.set_task_build(task)
            self.runq.propagate_runq_task_build()
            remaining = self.runq.number_of_tasks_to_build()
            debug("%d tasks remains after adding rmwork"%remaining)
            recipes = self.runq.get_recipes_with_tasks_to_build()

        print "The following will be build:"
        text = []
        for recipe in recipes:
            if recipe[1] == "machine":
                text.append("%s(%d)"%(recipe[2], recipe[4]))
            else:
                text.append("%s:%s(%d)"%(recipe[1], recipe[2], recipe[4]))
        print oelite.util.format_textblock(" ".join(text))

        self.cookbook.compute_recipe_build_priorities()

        if os.isatty(sys.stdin.fileno()) and not self.options.yes:
            while True:
                try:
                    response = raw_input("Do you want to continue [Y/n/?/??]? ")
                except KeyboardInterrupt:
                    response = "n"
                    print ""
                if response == "" or response[0] in ("y", "Y"):
                    break
                elif response == "?":
                    tasks = self.runq.get_tasks_to_build_description()
                    for task in tasks:
                        print "  " + task
                    continue
                elif response == "??":
                    tasks = self.runq.get_tasks_to_build_description(hashinfo=True)
                    for task in tasks:
                        print "  " + task
                    continue
                else:
                    info("Maybe next time")
                    return 0

        # FIXME: add some kind of statistics, with total_tasks,
        # prebaked_tasks, running_tasks, failed_tasks, done_tasks
        #
        # FIXME: add back support for options.fake_build
        rusage = oelite.profiling.Rusage("Build")
        exitcode = 0
        pending = PriorityQueue(initial = self.runq.get_runabletasks(),
                                key = lambda t: (-t.recipe.build_prio, t.recipe.remaining_tasks))

        oven = OEliteOven(self)
        try:
            while oven.count < oven.total:
                new_runable = self.runq.get_runabletasks()
                for t in new_runable:
                    pending.push(t)
                if not pending or oven.capacity <= 0:
                    # If we have no runable tasks and nothing in the
                    # oven, some tasks must have failed.
                    if not oven.currently_baking():
                        break
                    # Gotta wait for some task to finish. That may
                    # make some new task eligible.
                    oven.wait_any(False)
                    continue
                task = pending.pop()
                oven.start(task)
                # After starting a task, always do an immediate poll -
                # if it was a synchronous task, it is already done by
                # the time oven.start() returns, so it might as well get
                # removed from the oven and its dependents made
                # eligible.
                #
                # Rather than doing oven.wait_task(True, task), we
                # actually do a (single) poll for every task in the
                # oven. This is necessary to ensure that an important
                # task such as glibc:do_configure doesn't lie around
                # as a zombie while we do lots of do_fetch etc. - we
                # want the glibc recipe to proceed as fast as
                # possible, so that other recipes'
                # do_stage,do_configure and so on become eligible.
                oven.wait_all(True)
        finally:
            oven.wait_all(False)

        rusage.end()
        oven.write_profiling_data()

        for task in oven.failed_tasks:
            exitcode = 1
            print "\nERROR: %s failed  %s"%(task,task.logfn)
            if self.debug_loglines:
                with open(task.logfn, 'r') as fin:
                    if self.debug_loglines < 0:
                        print fin.read()
                    else:
                        print ''.join(fin.readlines()[-self.debug_loglines:])
        return exitcode

    def setup_tmpdir(self):

        tmpdir = os.path.realpath(self.config.get("TMPDIR", 1) or "tmp")
        #debug("TMPDIR = %s"%tmpdir)

        try:

            if not os.path.exists(tmpdir):
                os.makedirs(tmpdir)

            if (os.path.islink(tmpdir) and
                not os.path.exists(os.path.realpath(tmpdir))):
                os.makedirs(os.path.realpath(tmpdir))

        except Exception, e:
            die("failed to setup TMPDIR: %s"%e)
            import traceback
            e.print_exception(type(e), e, True)

        return


    def find_prebaked_package(self, package):
        """return full-path filename string or None"""
        package_deploy_dir = self.config.get("PACKAGE_DEPLOY_DIR")
        prebake_url_cache_dir = self.config.get("PREBAKE_CACHE_DIR")
        if not package_deploy_dir:
            die("PACKAGE_DEPLOY_DIR not defined")
        if self.options.prebake:
            prebake_path = self.config.get("PREBAKE_PATH") or []
            if prebake_path:
                prebake_path = prebake_path.split(":")
            prebake_path.insert(0, package_deploy_dir)
            prebake_path.insert(0, prebake_url_cache_dir)
        else:
            prebake_path = [package_deploy_dir]
        debug("package=%s"%(repr(package)))
        recipe = self.cookbook.get_recipe(package=package)
        if not recipe:
            raise NoSuchRecipe()
        metahash = self.runq.get_package_metahash(package)
        debug("got metahash=%s"%(metahash))
        package = self.cookbook.get_package(id=package)
        if not package:
            raise NoSuchPackage()
        filename = "%s_%s_%s.tar"%(package.name, recipe.version, metahash)
        debug("prebake_path=%s"%(prebake_path))
        #test local paths first
        for base_dir in prebake_path:
            path = os.path.join(
                base_dir,
                package.type,
                package.arch + (package.recipe.meta.get("EXTRA_ARCH") or ""),
                filename)
            debug("checking for prebake: %s"%(path))
            if os.path.exists(path):
                debug("found prebake: %s"%(path))
                return path
        #then test URLs from PREBAKE_URL
        url_prefix = self.config.get("PREBAKE_URL")
        if url_prefix is not None:
            package_path =os.path.join(
                    package.type,
                    package.arch + (package.recipe.meta.get("EXTRA_ARCH") or ""),
                    filename)
            downloaded_file =os.path.join(
                    prebake_url_cache_dir,
                    package_path)
            url = os.path.join(url_prefix, package_path)
            if oelite.fetch.url.grab(url, downloaded_file, timeout=1, retry=1):
                if os.path.exists(downloaded_file) and os.path.getsize(downloaded_file) > 0:
                    debug("using prebake from web: %s"%(url))
                    return downloaded_file
                else:
                    os.unlink(downloaded_file)
        return None


    def normpath(self, path):
        topdir = self.config.get("TOPDIR")
        if path.startswith(topdir):
            topdir = path[len(topdir)+1:]
        return topdir
