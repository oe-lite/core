import oebakery
from oebakery import die, err, warn, info, debug
from oelite import *
import sys, os, glob, shutil, datetime

from db import OEliteDB
from recipe import OEliteRecipe
from runq import OEliteRunQueue
import oelite.data, oelite.util, oelite.arch

import bb.parse, bb.utils, bb.build, bb.fetch

BB_ENV_WHITELIST = [
    "PATH",
    "PWD",
    "SHELL",
    "TERM",
]

OE_IMPORTS = [
    "oe.path",
    "oe.utils",
    "oe.packagegroup",
    "sys",
    "os",
    "time"
]

def setup_oeImports():
    def inject(name, value):
        """Make a python object accessible from the metadata"""
        if hasattr(bb.utils, "_context"):
            bb.utils._context[name] = value
        else:
            __builtins__[name] = value
    for toimport in OE_IMPORTS:
        imported = __import__(toimport)
        inject(toimport.split(".", 1)[0], imported)

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


def _parse(f, data, include=False):
    try:
        return bb.parse.handle(f, data, include)
    except (IOError, bb.parse.ParseError) as exc:
        die("unable to parse %s: %s" % (f, exc))


class OEliteBaker:

    def __init__(self, options, args, config):

        self.options = options

        self.config = config.createCopy()
        self.import_env()
        self.config = _parse("conf/bitbake.conf", self.config)

        oelite.arch.init(self.config)

        # Handle any INHERITs and inherit the base class
        inherits  = ["base"] + (self.config.getVar("INHERIT", 1) or "").split()
        # and inherit rmwork when needed
        try:
            rmwork = self.options.rmwork
            inherits.append("rmwork")
            if rmwork is None:
                rmwork = self.config.getVar("RMWORK", True)
                if rmwork == "0":
                    rmwork = False
            if rmwork:
                debug("rmwork")
                self.options.rmwork = True
        except AttributeError:
            pass
        for inherit in inherits:
            self.config = _parse("classes/%s.bbclass"%(inherit),
                                 self.config, 1)

        bb.fetch.fetcher_init(self.config)

        # things (ritem, item, recipe, or package) to do
        if args:
            self.things_todo = args
        elif "BB_DEFAULT_THING" in self.config:
            self.things_todo = self.config.getVar("BB_DEFAULT_THING", 1).split()
        else:
            self.things_todo = [ "base-rootfs" ]

        self.appendlist = {}
        self.db = OEliteDB()
        self.prepare_cookbook()

        return


    def __del__(self):
        return


    def import_env(self):
        whitelist = BB_ENV_WHITELIST
        if "BB_ENV_WHITELIST" in os.environ:
            whitelist += os.environ["BB_ENV_WHITELIST"].split()
        if "BB_ENV_WHITELIST" in self.config:
            whitelist += self.config.getVar("BB_ENV_WHITELIST", True).split()
        debug("whitelist=%s"%(whitelist))
        for var in set(os.environ).difference(whitelist):
            del os.environ[var]
        if oebakery.DEBUG:
            debug("Whitelist filtered shell environment:")
            for var in os.environ:
                debug("> %s=%s"%(var, os.environ[var]))
        for var in whitelist:
            if not var in self.config and var in os.environ:
                self.config[var] = os.environ[var]
                debug("importing %s=%s"%(var, os.environ[var]))
        return


    def prepare_cookbook(self):

        self.cookbook = {}

        # collect all available .bb files
        bbrecipes = self.list_bbrecipes()

        #setup oe-lite imports
        setup_oeImports()
        
        # parse all .bb files
        total = len(bbrecipes)
        parsed = 0
        start = datetime.datetime.now()
        for bbrecipe in bbrecipes:
            if not self.options.quiet:
                progress_info("Parsing recipe files", total, parsed)
            data = self.parse_recipe(bbrecipe)
            for extend in data:
                recipe = OEliteRecipe(bbrecipe, extend, data[extend], self.db)
                self.cookbook[recipe.id] = recipe
            parsed += 1
        if not self.options.quiet:
            progress_info("Parsing recipe files", total, parsed)
        if oebakery.DEBUG:
            timing_info("Parsing", start)
        return

    def show(self):

        if len(self.things_todo) == 0:
            die("you must specify something to show")
        elif len(self.things_todo) > 1:
            die("can only show one thing at a time")

        search = self.things_todo[0].split("_", 1)

        if len(search) == 1:
            search.append(None)

        debug("looking for %s"%(repr(search)))
        recipes = self.db.get_recipe_id(name=search[0], version=search[1],
                                        multiple=True)
        debug("recipes=%s %s"%(repr(recipes),
                               repr(self.db.get_recipe(recipes[0]))))

        if not recipes:
            die("no recipe found")
        elif len(recipes) > 1:
            chosen = (recipes[0], self.db.get_recipe(recipes[0])[1])
            for other in recipes[1:]:
                debug("chosen=%s other=%s"%(chosen, other))
                version = self.db.get_recipe(other)[1]
                vercmp = bb.utils.vercmp_part(chosen[1], version)
                if vercmp < 0:
                    chosen = (other, version)
                if vercmp == 0:
                    debug("chosen=%s\nother=%s version=%s"%(chosen, other, version))
                    die("you have to be more precise")
            chosen = chosen[0]
        else:
            chosen = recipes[0]

        recipe = self.cookbook[chosen]

        if self.options.task:
            task_name = "do_" + self.options.task
            runq = OEliteRunQueue(self.db, self.cookbook, self.config)
            task_name = self.db.task_name_id(task_name)
            runq._add_recipe(chosen, task_name)

            recipe.prepare(runq, task_name)

        oelite.data.dump(d=recipe.data, pretty=True,
                         nohash=(not self.options.nohash))

        return 0


    def bake(self):

        self.setup_tmpdir()

        # task(s) to do
        if self.options.task:
            tasks_todo = self.options.task
        elif "BB_DEFAULT_TASK" in self.config:
            tasks_todo = self.config.getVar("BB_DEFAULT_TASK", 1)
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
            default_relax = self.config.getVar("DEFAULT_RELAX", 1)
            if default_relax and default_relax != "0":
                self.options.relax = int(default_relax)
            else:
                self.options.relax = None

        # init build quue
        runq = OEliteRunQueue(self.db, self.cookbook, self.config,
                              self.options.rebuild, self.options.relax)

        # first, add complete dependency tree, with complete
        # task-to-task and task-to-package/task dependency information
        debug("Building dependency tree")
        start = datetime.datetime.now()
        for thing in self.things_todo:
            for task in self.tasks_todo:
                task = "do_" + task
                try:
                    if not runq.add_something(thing, task):
                        die("No such thing: %s"%(thing))
                except RecursiveDepends, e:
                    die("dependency loop: %s\n\t--> %s"%(
                            e.args[1], "\n\t--> ".join(e.args[0])))
                except NoSuchTask, e:
                    die("No such task: %s: %s"%(thing, e.__str__()))
        if oebakery.DEBUG:
            timing_info("Building dependency tree", start)

        # update runq task list, checking recipe and src hashes and
        # determining which tasks needs to be run
        # examing each task, computing it's hash, and checking if the
        # task has already been built, and with the same hash.
        task = runq.get_metahashable_task()
        total = self.db.number_of_runq_tasks()
        count = 0
        start = datetime.datetime.now()
        while task:
            progress_info("Calculating task metadata hashes", total, count)
            recipe_id = self.db.get_recipe_id(task=task)
            recipe = self.cookbook[recipe_id]

            if self.db.is_task_nostamp(task):
                self.db.set_runq_task_metahash(task, "0")
                task = runq.get_metahashable_task()
                count += 1
                continue

            datahash = recipe.datahash()
            srchash = recipe.srchash()

            dephashes = {}
            task_dependencies = runq.task_dependencies(task)
            for depend in task_dependencies[0]:
                dephashes[depend] = self.db.get_runq_task_metahash(depend)
            for depend in [d[0] for d in task_dependencies[1]]:
                dephashes[depend] = self.db.get_runq_task_metahash(depend)
            for depend in [d[0] for d in task_dependencies[2]]:
                dephashes[depend] = self.db.get_runq_task_metahash(depend)

            import hashlib

            hasher = hashlib.md5()
            hasher.update(str(sorted(dephashes.values())))
            dephash = hasher.hexdigest()

            hasher = hashlib.md5()
            hasher.update(datahash)
            hasher.update(srchash)
            hasher.update(dephash)
            metahash = hasher.hexdigest()

            #if oebakery.DEBUG:
            #    recipe_name = self.db.get_recipe(recipe_id)
            #    task_name = self.db.get_task(task=task)
            #    debug(" %d %s:%s data=%s src=%s dep=%s meta=%s"%(
            #            task, "_".join(recipe_name), task_name,
            #            datahash, srchash, dephash, metahash))

            recipe_name = self.db.get_recipe_name(recipe_id)
            task_name = self.db.get_task(task=task)

            self.db.set_runq_task_metahash(task, metahash)

            (mtime, tmphash) = self.read_task_stamp(task, recipe.data)
            if not mtime:
                self.db.set_runq_task_build(task)
            else:
                self.db.set_runq_task_stamp(task, mtime, tmphash)

            task = runq.get_metahashable_task()
            count += 1
            continue

        progress_info("Calculating task metadata hashes", total, count)

        if oebakery.DEBUG:
            timing_info("Calculation task metadata hashes", start)

        if count != total:
            die("Circular dependencies I presume.  Add more debug info!")

        self.db.set_runq_task_build_on_nostamp_tasks()
        self.db.set_runq_task_build_on_retired_tasks()
        self.db.set_runq_task_build_on_hashdiff()

        # check for availability of prebaked packages, and set package
        # filename for all packages.
        depend_packages = self.db.get_runq_depend_packages()
        rdepend_packages = self.db.get_runq_rdepend_packages()
        depend_packages = set(depend_packages).union(rdepend_packages)
        for package in depend_packages:
            # FIXME: skip this package if it is to be rebuild
            prebake = self.find_prebaked_package(package)
            if prebake:
                self.db.set_runq_package_filename(package, prebake,
                                                  prebake=True)

        # clear parent_task for all runq_depends where all runq_depend
        # rows with the same parent_task has prebake flag set
        self.db.prune_prebaked_runq_depends()

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
        # the above after all :-( We will now have som runq_depends
        # with parent_task.prebake flag set, but when we follow its
        # dependencies, we will find one or more recipes that has to
        # be rebuilt, fx. because of a --rebuild flag.

        self.db.propagate_runq_task_build()

        build_count = self.db.set_runq_buildhash_for_build_tasks()
        nobuild_count = self.db.set_runq_buildhash_for_nobuild_tasks()
        if (build_count + nobuild_count) != total:
            die("build_count + nobuild_count != total")


        deploy_dir = self.config.getVar("PACKAGE_DEPLOY_DIR", True)
        packages = self.db.get_runq_packages_to_build()
        for package in packages:
            (package_name, package_arch) = self.db.get_package(package)
            (recipe_name, recipe_version) = self.db.get_recipe(
                {"package": package})
            buildhash = self.db.get_runq_package_buildhash(package)
            filename = os.path.join(
                deploy_dir, package_arch,
                "%s_%s_%s.tar"%(package_name, recipe_version, buildhash))
            debug("will use from build: %s"%(filename))
            self.db.set_runq_package_filename(package, filename)

        self.db.mark_primary_runq_depends()
        self.db.prune_runq_depends_nobuild()
        self.db.prune_runq_depends_with_nobody_depending_on_it()
        self.db.prune_runq_tasks()

        remaining = self.db.number_of_tasks_to_build()
        debug("%d tasks remains"%remaining)

        recipes = self.db.get_recipes_with_tasks_to_build()
        if not recipes:
            info("Nothing to do")
            return 0

        if self.options.rmwork:
            for recipe in recipes:
                if (tasks_todo != ["build"]
                    and self.db.is_runq_recipe_primary(recipe[0])):
                    debug("skipping...")
                    continue
                debug("adding %s:do_rmwork"%(recipe[1]))
                runq._add_recipe(recipe[0], "do_rmwork")
                self.db.set_runq_task_build({"recipe": recipe[0], "task": "do_rmwork"})
            self.db.propagate_runq_task_build()
            remaining = self.db.number_of_tasks_to_build()
            debug("%d tasks remains after adding rmwork"%remaining)
            recipes = self.db.get_recipes_with_tasks_to_build()

        print "The following will be build:"
        text = []
        for recipe in recipes:
            text.append("%s(%d)"%(recipe[1], recipe[3]))
        print oelite.util.format_textblock(" ".join(text))

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
                    tasks = self.db.get_tasks_to_build_description()
                    for task in tasks:
                        print "  " + task
                    continue
                elif response == "??":
                    tasks = self.db.get_tasks_to_build_description(hashinfo=True)
                    for task in tasks:
                        print "  " + task
                    continue
                else:
                    info("Maybe next time")
                    return 0

        # FIXME: add some kind of statistics, with total_tasks,
        # prebaked_tasks, running_tasks, failed_tasks, done_tasks
        task = runq.get_runabletask()
        start = datetime.datetime.now()
        total = self.db.number_of_tasks_to_build()
        count = 0
        exitcode = 0
        while task:
            count += 1
            recipe_id = self.db.get_recipe_id(task=task)
            recipe_name = self.db.get_recipe_name(recipe_id)
            recipe = self.cookbook[recipe_id]
            task_name = self.db.get_task(task=task)
            debug("")
            debug("Preparing %s:%s"%(recipe_name, task_name))
            data = recipe.prepare(runq, task)
            info("Running %d / %d %s:%s"%(count, total, recipe_name, task_name))
            self.task_build_started(task, data)
            if exec_func(task_name, data):
                self.task_build_done(task, data,
                                     self.db.get_runq_buildhash(task))
                runq.mark_done(task)
            else:
                err("%s:%s failed"%(recipe_name, task_name))
                exitcode = 1
                self.task_build_failed(task, data)
                # FIXME: support command-line option to abort on first
                # failed task
            task = runq.get_runabletask()
        timing_info("Build", start)

        return exitcode


    def setup_tmpdir(self):

        tmpdir = os.path.realpath(self.config.getVar("TMPDIR", 1) or "tmp")
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


    def list_bbrecipes(self):

        BBRECIPES = (self.config["BBRECIPES"] or "").split(":")

        if not BBRECIPES:
            die("BBRECIPES not defined")

        newfiles = set()
        for f in BBRECIPES:
            if os.path.isdir(f):
                dirfiles = find_bbrecipes(f)
                newfiles.update(dirfiles)
            else:
                globbed = glob.glob(f)
                if not globbed and os.path.exists(f):
                    globbed = [f]
                newfiles.update(globbed)

        bbrecipes = []
        bbappend = []
        for f in newfiles:
            if f.endswith(".bb"):
                bbrecipes.append(f)
            elif f.endswith(".bbappend"):
                bbappend.append(f)
            else:
                warn("skipping %s: unknown file extension"%(f))

        appendlist = {}
        for f in bbappend:
            base = os.path.basename(f).replace(".bbappend", ".bb")
            if not base in appendlist:
                appendlist[base] = []
            appendlist[base].append(f)

        return bbrecipes


    def parse_recipe(self, recipe):
        path = os.path.abspath(recipe)
        return bb.parse.handle(path, self.config.createCopy())


    def stampfile_path(self, task, data):
        task_name = self.db.get_task(task=task)
        stampdir = data.getVar("STAMPDIR", True)
        return (stampdir, os.path.join(stampdir, task_name))


    # return (mtime, hash) from stamp file
    def read_task_stamp(self, task, data):
        stampfile = self.stampfile_path(task, data)[1]
        if not os.path.exists(stampfile):
            return (None, None)
        if not os.path.isfile(stampfile):
            die("bad hash file: %s"%(stampfile))
        if os.path.getsize(stampfile) == 0:
            return (None, None)
        mtime = os.stat(stampfile).st_mtime
        with open(stampfile, "r") as stampfile:
            tmphash = stampfile.read()
        return (mtime, tmphash)


    def task_build_started(self, task, data):
        if self.db.is_task_nostamp(task):
            return
        (stampdir, stampfile) = self.stampfile_path(task, data)
        if not os.path.exists(stampdir):
            os.makedirs(stampdir)
        open(stampfile, "w").close()
        return


    def task_build_done(self, task, data, buildhash):
        if self.db.is_task_nostamp(task):
            return
        (stampdir, stampfile) = self.stampfile_path(task, data)
        if not os.path.exists(stampdir):
            os.makedirs(stampdir)
        with open(stampfile, "w") as _stampfile:
            _stampfile.write(buildhash)
        return


    def task_build_failed(self, task, data):
        return


    def task_cleaned(self, task, data):
        hashpath = self.stampfile_path(task, data)
        if os.path.exists(hashpath):
            os.remove(hashpath)


    def find_prebaked_package(self, package):
        """return full-path filename string or None"""
        package_deploy_dir = self.config.getVar("PACKAGE_DEPLOY_DIR", True)
        if not package_deploy_dir:
            die("PACKAGE_DEPLOY_DIR not defined")
        if self.options.prebake:
            prebake_path = self.config.getVar("PREBAKE_PATH", True) or []
            if prebake_path:
                prebake_path = prebake_path.split(":")
            prebake_path.insert(0, package_deploy_dir)
        else:
            prebake_path = [package_deploy_dir]
        debug("package=%s"%(repr(package)))
        recipe = self.db.get_recipe({"package": package})
        if not recipe:
            raise NoSuchRecipe()
        (recipe, version) = recipe
        metahash = self.db.get_runq_package_metahash(package)
        debug("got metahash=%s"%(metahash))
        package = self.db.get_package(package)
        if not package:
            raise NoSuchPackage()
        (name, arch) = package
        filename = "%s_%s_%s.tar"%(name, version, metahash)
        debug("prebake_path=%s"%(prebake_path))
        for base_dir in prebake_path:
            debug("base_dir=%s, arch=%s, filename=%s"%(base_dir, arch, filename))
            path = os.path.join(base_dir, arch, filename)
            debug("checking for prebake: %s"%(path))
            if os.path.exists(path):
                debug("found prebake: %s"%(path))
                return path
        return None

def exec_func(func, data):

    body = data.getVar(func, True)
    if not body:
        return True

    flags = data.getVarFlags(func)
    for item in ['deps', 'check', 'interactive', 'python', 'fakeroot',
                 'cleandirs', 'dirs']:
        if not item in flags:
            flags[item] = None

    ispython = flags['python']

    cleandirs = flags['cleandirs']
    if cleandirs:
        cleandirs = data.expand(cleandirs, None).split()
    if cleandirs:
        for cleandir in cleandirs:
            if not os.path.exists(cleandir):
                continue
            try:
                debug("cleandir %s"%(cleandir))
                shutil.rmtree(cleandir)
            except Exception, e:
                err("cleandir %s failed: %s"%(cleandir, e))
                return False

    dirs = flags['dirs']
    if dirs:
        dirs = data.expand(dirs, None).split()

    if dirs:
        for adir in dirs:
            bb.utils.mkdirhier(adir)
        adir = dirs[-1]
    else:
        adir = data.getVar('B', True)

    # Save current directory
    try:
        prevdir = os.getcwd()
    except OSError:
        prevdir = data.getVar('TOPDIR', True)

    # Setup logfiles
    t = data.getVar('T', 1)
    if not t:
        die("T variable not set, unable to build")
    bb.utils.mkdirhier(t)
    logfile = "%s/log.%s.%s" % (t, func, str(os.getpid()))
    runfile = "%s/run.%s.%s" % (t, func, str(os.getpid()))

    # Change to correct directory (if specified)
    if adir and os.access(adir, os.F_OK):
        os.chdir(adir)

    # stdin
    si = file('/dev/null', 'r')

    # stdout
    try:
        if oebakery.DEBUG or ispython:
            so = os.popen("tee \"%s\"" % logfile, "w")
        else:
            so = file(logfile, 'w')
    except OSError:
        logger.exception("Opening log file '%s'", logfile)
        pass

    # stderr
    se = so

    # Dup the existing fds so we dont lose them
    osi = [os.dup(sys.stdin.fileno()), sys.stdin.fileno()]
    oso = [os.dup(sys.stdout.fileno()), sys.stdout.fileno()]
    ose = [os.dup(sys.stderr.fileno()), sys.stderr.fileno()]

    # Replace those fds with our own
    os.dup2(si.fileno(), osi[1])
    os.dup2(so.fileno(), oso[1])
    os.dup2(se.fileno(), ose[1])

    # FIXME: why?
    os.umask(022)

    try:
        # Run the function
        retval = False
        if ispython:
            retval = exec_func_python(func, data, runfile, logfile)
        else:
            retval = exec_func_shell(func, data, runfile, logfile, flags)

    finally:

        # Restore original directory
        try:
            os.chdir(prevdir)
        except:
            pass

        # Restore the backup fds
        os.dup2(osi[0], osi[1])
        os.dup2(oso[0], oso[1])
        os.dup2(ose[0], ose[1])

        # Close our logs
        si.close()
        so.close()
        se.close()

        if os.path.exists(logfile) and os.path.getsize(logfile) == 0:
            #debug("Removing zero size logfile: %s"%logfile)
            os.remove(logfile)

        # Close the backup fds
        os.close(osi[0])
        os.close(oso[0])
        os.close(ose[0])

    return retval


def exec_func_python(func, data, runfile, logfile):
    """Execute a python BB 'function'"""

    bbfile = data.getVar("FILE", True)
    tmp  = "def " + func + "(d):\n%s" % data.getVar(func, True)
    tmp += '\n' + func + '(d)'

    f = open(runfile, "w")
    f.write(tmp)
    comp = None
    try:
        comp = bb.utils.better_compile(tmp, func, bbfile)
    except:
        die("compiling %s failed, ask an OE-lite wizard to add more debug information"%func)
    try:
        bb.utils.better_exec(comp, {"d": data}, tmp, bbfile)
    except:
        err("executing python function %s failed"%(func))
        if oebakery.DEBUG:
            raise
        return False
        #if sys.exc_info()[0] in (bb.parse.SkipPackage, bb.build.FuncFailed):
        #    raise
        ##return False
        #raise

    return True


def exec_func_shell(func, data, runfile, logfile, flags):
    """Execute a shell BB 'function' Returns true if execution was successful.

    For this, it creates a bash shell script in the tmp dectory,
    writes the local data into it and finally executes. The output of
    the shell will end in a log file and stdout.

    Note on directory behavior.  The 'dirs' varflag should contain a list
    of the directories you need created prior to execution.  The last
    item in the list is where we will chdir/cd to.
    """

    deps = flags['deps']
    check = flags['check']
    if check in globals():
        if globals()[check](func, deps):
            return

    f = open(runfile, "w")
    f.write("#!/bin/sh -e\n")
    #if oebakery.DEBUG:
    #    f.write("set -x\n")
    bb.data.emit_env(f, data)

    f.write("cd %s\n" % os.getcwd())
    if func: f.write("%s\n" % func)
    f.close()
    os.chmod(runfile, 0775)
    if not func:
        raise TypeError("Function argument must be a string")

    # execute function
    if flags['fakeroot']:
        maybe_fakeroot = "PATH=\"%s\" %s " % (data.getVar("PATH", True),
                                              data.getVar("FAKEROOT", True)
                                              or "fakeroot")
    else:
        maybe_fakeroot = ''
    lang_environment = "LC_ALL=C "
    ret = os.system('%s%ssh -e %s'%(lang_environment, maybe_fakeroot, runfile))

    if ret == 0:
        return True

    return False


def progress_info(msg, total, current):
    if os.isatty(sys.stdout.fileno()):
        fieldlen = len(str(total))
        template = "\r%s: %%%dd / %%%dd [%2d %%%%]"%(msg, fieldlen, fieldlen,
                                                 current*100//total)
        #sys.stdout.write("\r%s: %04d/%04d [%2d %%]"%(
        sys.stdout.write(template%(current, total))
        if current == total:
            sys.stdout.write("\n")
        sys.stdout.flush()
    else:
        if current == 0:
            sys.stdout.write("%s, please wait..."%(msg))
        elif current == total:
            sys.stdout.write("done.\n")
        sys.stdout.flush()


def timing_info(msg, start):
    msg += " time "
    delta = datetime.datetime.now() - start
    hours = delta.seconds // 3600
    minutes = delta.seconds // 60 % 60
    seconds = delta.seconds % 60
    milliseconds = delta.microseconds // 1000
    if hours:
        msg += "%dh%02dm%02ds"%(hours, minutes, seconds)
    elif minutes:
        msg += "%dm%02ds"%(minutes, seconds)
    else:
        msg += "%d.%03d seconds"%(seconds, milliseconds)
    info(msg)
    return
