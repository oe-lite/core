import oebakery
from oebakery import die, err, warn, info, debug
from oelite import *
import sys, os, glob, shutil, datetime

from db import OEliteDB
from recipe import OEliteRecipe
from runq import OEliteRunQueue

import bb.parse, bb.utils, bb.build, bb.fetch

BB_ENV_WHITELIST = [
    "COLORTERM",
    "DBUS_SESSION_BUS_ADDRESS",
    "DESKTOP_SESSION",
    "DESKTOP_STARTUP_ID",
    "DISPLAY",
    "GNOME_KEYRING_PID",
    "GNOME_KEYRING_SOCKET",
    "GPG_AGENT_INFO",
    "GTK_RC_FILES",
    "HOME",
    "LANG",
    "LOGNAME",
    "PATH",
    "PWD",
    "SESSION_MANAGER",
    "SHELL",
    "SSH_AUTH_SOCK",
    "TERM",
    "USER",
    "USERNAME",
    "_",
    "XAUTHORITY",
    "XDG_DATA_DIRS",
    "XDG_SESSION_COOKIE",
]

def add_parser_options(parser):
    parser.add_option("-t", "--task",
                      action="store", type="str", default=None,
                      help="task(s) to do")
    return


def _parse(f, data, include=False):
    try:
        return bb.parse.handle(f, data, include)
    except (IOError, bb.parse.ParseError) as exc:
        die("unable to parse %s: %s" % (f, exc))


class OEliteBaker:

    def __init__(self, config):

        self.config = config.createCopy()

        self.import_env()

        self.config = _parse("conf/bitbake.conf", self.config)

        # Handle any INHERITs and inherit the base class
        inherits  = ["base"] + (config.getVar("INHERIT", 1) or "").split()
        for inherit in inherits:
            self.config = _parse("classes/%s.bbclass"%(inherit),
                                 self.config, 1)

        bb.fetch.fetcher_init(self.config)

        self.appendlist = {}
        self.db = OEliteDB()
        self.prepare_cookbook()
        self.buildhash = {}

        return


    def __del__(self):
        return


    def import_env(self):
        whitelist = BB_ENV_WHITELIST
        if "BB_ENV_EXTRAWHITE" in os.environ:
            whitelist += os.environ["BB_ENV_EXTRAWHITE"].split()
        if "BB_ENV_EXTRAWHITE" in self.config:
            whitelist += self.config["BB_ENV_EXTRAWHITE"].split()
        for var in whitelist:
            if not var in self.config and var in os.environ:
                self.config[var] = os.environ[var]
                debug("importing env %s=%s"%(var, os.environ[var]))
        return


    def prepare_cookbook(self):

        self.cookbook = {}

        # collect all available .bb files
        bbrecipes = self.list_bbrecipes()

        # parse all .bb files
        total = len(bbrecipes)
        parsed = 0
        start = datetime.datetime.now()
        for bbrecipe in bbrecipes:
            progress_info("Parsing recipe files", total, parsed)
            data = self.parse_recipe(bbrecipe)
            for extend in data:
                recipe = OEliteRecipe(bbrecipe, extend, data[extend], self.db)
                self.cookbook[recipe.id] = recipe
            parsed += 1
        progress_info("Parsing recipe files", total, parsed)
        if oebakery.DEBUG:
            timing_info("Parsing", start)

        return


    def bake(self, options, args):

        self.setup_tmpdir()

        # task(s) to do
        if options.task:
            tasks_todo = options.task.split(",")
        elif "BB_DEFAULT_TASK" in self.config:
            tasks_todo = self.config.getVar("BB_DEFAULT_TASK", 1).split(",")
        else:
            #tasks_todo = [ "all" ]
            tasks_todo = [ "build" ]

        # things (ritem, item, recipe, or package) to do
        if args:
            things_todo = args
        elif "BB_DEFAULT_THING" in self.config:
            things_todo = self.config.getVar("BB_DEFAULT_THING", 1).split()
        else:
            things_todo = [ "base-rootfs" ]

        # setup build quue
        runq = OEliteRunQueue(self.db, self.cookbook, self.config)

        # first, add complete dependency tree, with complete
        # task-to-task dependency information
        debug("Building dependency tree")
        start = datetime.datetime.now()
        for thing in things_todo:
            for task in tasks_todo:
                task = "do_" + task
                try:
                    if not runq.add_something(thing, task):
                        die("failed to add %s:%s to runqueue"%(thing, task))
                except RecursiveDepends, e:
                    #die("recursive dependency detected: %s %s"%(type(e), e))
                    die("dependency loop: %s\n\t--> %s"%(
                            e.args[1], "\n\t--> ".join(e.args[0])))
        if oebakery.DEBUG:
            timing_info("Building dependency tree", start)

        # update runq task list, checking recipe and src hashes and
        # determining which tasks needs to be run
        # examing each task, computing it's hash, and checking if the
        # task has already been built, and with the same hash.
        task = runq.get_hashabletask()
        total = self.db.number_of_runq_tasks()
        count = reuse = rebuild = partial = pristine = 0
        start = datetime.datetime.now()
        while task:
            progress_info("Checking task status", total, count)
            recipe_id = self.db.get_recipe_id(task=task)
            recipe = self.cookbook[recipe_id]

            datahash = recipe.datahash()

            srchash = recipe.srchash()

            dephashes = {}
            for depend in runq.task_dependencies(task):
                dephashes[depend] = self.db.get_runq_task_hash(depend)

            import hashlib

            hasher = hashlib.md5()
            hasher.update(str(dephashes))
            dephash = hasher.hexdigest()

            hasher = hashlib.md5()
            hasher.update(datahash)
            hasher.update(srchash)
            hasher.update(dephash)
            buildhash = hasher.hexdigest()
            self.buildhash[task] = buildhash

            recipe_name = self.db.get_recipe_name(recipe_id)
            task_name = self.db.get_task(task=task)
            #debug("datahash=%s srchash=%s dephash=%s buildhash=%s %d %s:%s"%(
            #        datahash, srchash, dephash, buildhash, task, recipe_name, task_name))

            self.db.set_runq_task_hash(task, buildhash)

            # check for existing build, ie. read the task hash file
            # if it exists, but is empty, a partial build is assume
            # if it exists, and hash matches, the task is considered done
            # if it exists, but hash does not match, task must be rebuilt
            status = self.get_task_status(task, recipe.data, buildhash)
            recipe_name = self.db.get_recipe({"task": task})
            task_name = self.db.get_task(task=task)
            if status == 0:
                # task has been built with matching hash
                debug("reusing task %d %s:%s"%(task, recipe_name, task_name))
                runq.mark_done(task, delete=False)
                reuse += 1
                pass
            elif status == 1:
                # task built, but with different hash
                debug("task needs to be rebuild  %d %s:%s"%(task, recipe_name, task_name))
                rebuild += 1
                pass
            elif status == 2:
                # task partial built
                debug("partially built task %d %s:%s"%(task, recipe_name, task_name))
                partial += 1
                pass
            else:
                # task has not been built
                debug("pristine task %d %s:%s"%(task, recipe_name, task_name))
                pristine += 1
                pass

            task = runq.get_hashabletask()

            count += 1
            continue

        progress_info("Checking task status", total, count)
        build = rebuild + partial + pristine
        info("%d tasks to run, %d tasks does not have to be run"%(
                build, reuse))
        if oebakery.DEBUG:
            timing_info("Task checking", start)

        self.db.prune_done_tasks()

        #runq.update_tasks()

        # FIXME: add some kind of statistics, with total_tasks,
        # prebaked_tasks, running_tasks, failed_tasks, done_tasks
        task = runq.get_runabletask()
        start = datetime.datetime.now()
        while task:
            recipe_id = self.db.get_recipe_id(task=task)
            recipe_name = self.db.get_recipe_name(recipe_id)
            recipe = self.cookbook[recipe_id]
            task_name = self.db.get_task(task=task)
            debug("")
            debug("Preparing %s:%s"%(recipe_name, task_name))
            recipe.prepare(runq)
            info("Running %s:%s"%(recipe_name, task_name))
            self.task_build_started(task, recipe.data)
            if exec_func(task_name, recipe.data):
                self.task_build_done(task, recipe.data, self.buildhash[task])
                runq.mark_done(task)
            else:
                warn("%s:%s failed"%(recipe_name, task_name))
                self.task_build_failed(task, recipe.data)
                # FIXME: support command-line option to abort on first
                # failed task
            task = runq.get_runabletask()
        if build:
            timing_info("Build", start)

        return 0


    def setup_tmpdir(self):

        tmpdir = os.path.abspath(self.config.getVar("TMPDIR", 1) or "tmp")
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

    # parse conf/bitbake.conf

    # collect all available .bb files

    # parse all .bb files


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


    def hashfile_path(self, task, data):
        task_name = self.db.get_task(task=task)
        hashbase = data.getVar("HASHDIR", True)
        return (hashbase, os.path.join(hashbase, task_name))


    def get_task_status(self, task, data, buildhash):
        hashpath = self.hashfile_path(task, data)[1]
        if not os.path.exists(hashpath):
            return 3
        if not os.path.isfile(hashpath):
            die("bad hash file: %s"%(hashpath))
        if os.path.getsize(hashpath) == 0:
            return 2
        with open(hashpath, "r") as hashfile:
            oldhash = hashfile.read()
        if oldhash != buildhash:
            return 1
        return 0


    def task_build_started(self, task, data):
        (hashdir, hashfile) = self.hashfile_path(task, data)
        if not os.path.exists(hashdir):
            os.makedirs(hashdir)
        open(hashfile, "w").close()
        return


    def task_build_done(self, task, data, buildhash):
        (hashdir, hashfile) = self.hashfile_path(task, data)
        if not os.path.exists(hashdir):
            os.makedirs(hashdir)
        with open(hashfile, "w") as _hashfile:
            oldhash = _hashfile.write(buildhash)
        return


    def task_build_failed(self, task, data):
        return


    def task_cleaned(self, task, data):
        hashpath = self.hashfile_path(task, data)
        if os.path.exists(hashpath):
            os.remove(hashpath)


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
    comp = bb.utils.better_compile(tmp, func, bbfile)
    try:
        bb.utils.better_exec(comp, {"d": data}, tmp, bbfile)
    except:
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
        msg += "%dh%02m%02s"%(hours, minutes, seconds)
    elif minutes:
        msg += "%dm%02s"%(minutes, seconds)
    else:
        msg += "%d.%03d"%(seconds, milliseconds)
    info(msg)
    return
