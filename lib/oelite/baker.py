import oebakery
from oebakery import die, err, warn, info, debug
from oelite import *
import sys, os
import glob, re

from db import OEliteDB
from recipe import OEliteRecipe
from runq import OEliteRunQueue

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

        self.config = _parse("conf/bitbake.conf", config)

        # Handle any INHERITs and inherit the base class
        inherits  = ["base"] + (config.getVar("INHERIT", 1) or "").split()
        for inherit in inherits:
            self.config = _parse("classes/%s.bbclass"%(inherit),
                                 self.config, 1)

        #bb.fetch.fetcher_init(self.config)

        self.appendlist = {}

        self.db = OEliteDB()

        self.prepare_cookbook()

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
                #debug("importing env %s=%s"%(var, os.environ[var]))
        return


    def prepare_cookbook(self):

        self.cookbook = {}

        # collect all available .bb files
        bbrecipes = self.list_bbrecipes()

        def parse_status(parsed):
            if os.isatty(sys.stdout.fileno()):
                sys.stdout.write("\rParsing recipe files: %04d/%04d [%2d %%]"%(
                        parsed, total, parsed*100//total))
                if parsed == total:
                    sys.stdout.write("\n")
                sys.stdout.flush()
            else:
                if parsed == 0:
                    sys.stdout.write("Parsing recipe files, please wait...")
                elif parsed == total:
                    sys.stdout.write("done.\n")
                sys.stdout.flush()

        # parse all .bb files
        total = len(bbrecipes)
        parsed = 0
        for bbrecipe in bbrecipes:
            parse_status(parsed)
            data = self.parse_recipe(bbrecipe)
            for extend in data:
                recipe = OEliteRecipe(bbrecipe, extend, data[extend], self.db)
                self.cookbook[recipe.id] = recipe
            parsed += 1
        parse_status(parsed)

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


        #tasks = self.db.db.execute(
        #    "SELECT task_name.name, recipe.name, runq_task.run, runq_task.done "
        #    "FROM runq_task, task, task_name, recipe "
        #    "WHERE runq_task.task=task.id AND task.name=task_name.id "
        #    "AND task.recipe=recipe.id ")
        #for task in tasks.fetchall():
        #    debug("runq_task %s:%s run=%s done=%s"%task)

        #tasks = self.db.db.execute(
        #    "SELECT * FROM runq_taskdepend")
        #for task in tasks.fetchall():
        #    debug("runq_taskdepend %s\t%s"%task)
        
        # update runq task list, checking recipe and src hashes and
        # determining which tasks needs to be run
        #runq.update_tasks()

        #runable_tasks = self.db.db.execute(
        #    "SELECT t.task, c.total, c.done "
        #    "FROM runq_task AS t, "
        #    "(SELECT task, "
        #    " COUNT(depend) AS total,"
        #    " COUNT(depend_hash) AS hashed,"
        #    " COUNT(depend_done) AS done"
        #    " FROM runq_taskdepend_view GROUP BY task) AS c "
        #    "WHERE t.task=c.task")
        #for runable in runable_tasks.fetchall():
        #    #debug("runq_taskdepend %s\t%s\t%s\t%s\t%s\t%s"%runable)
        #    debug("runq_taskdepend %s\t%s\t%s"%runable)

        #runable_tasks = self.db.db.execute(
        #    "SELECT * FROM runq_taskdepends_count WHERE total_depends=0")
        #for runable in runable_tasks.fetchall():
        #    #debug("runq_taskdepend %s\t%s\t%s\t%s\t%s\t%s"%runable)
        #    debug("runq_taskdepends_count %s\t%s\t%s\t%s\t%s\t%s"%runable)

        info("Processing runqueue:")
        task = runq.get_runabletask()
        while task:
            #debug("runable tasks:")
            #runable_tasks = self.db.db.execute(
            #    "SELECT * FROM runq_taskdepends_count")
            #for runable in runable_tasks.fetchall():
            #    debug("runq_taskdepend %s\t%s\t%s\t%s\t%s\t%s"%runable)
            recipe_name = self.db.get_recipe({"task": task})
            task_name = self.db.get_task(task=task)
            info("Running %s:%s"%(recipe_name,task_name))
            runq.mark_done(task)
            task = runq.get_runabletask()

        return 0


    def run_task(self, task):
        # FIXME: why?
        os.umask(022)

        return


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
        return bb.parse.handle(recipe, self.config.createCopy())
