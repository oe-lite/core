import oebakery
from oebakery import die, err, warn, info, debug
import oelite.meta
import oelite.recipe
from oelite.dbutil import *
import oelite.function
import bb.utils

import sys
import os
import warnings
import shutil
import re

def task_name(name):
    if name.startswith("do_"):
        return name
    return "do_" + name


class OEliteTask:

    TASKFUNC_RE = re.compile(r"^do_([a-z]+).*?")

    def __init__(self, id, recipe, name, nostamp, cookbook):
        self.id = id
        self.recipe = cookbook.get_recipe(id=recipe)
        self.name = name
        self.nostamp = nostamp
        self.cookbook = cookbook
        self.meta = None
        return

    def __str__(self):
        return "%s:%s"%(self.recipe, self.name)


    def get_parents(self):
        parents = flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT parent FROM task_parent WHERE recipe=? AND task=?",
            (self.recipe.id, self.name,)))
        if not parents:
            return []
        return self.cookbook.get_tasks(recipe=self.recipe, name=parents)

    def get_deptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT deptask FROM task_deptask WHERE task=?",
            (self.id,)))

    def get_rdeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT rdeptask FROM task_rdeptask WHERE task=?",
            (self.id,)))

    def get_recdeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT recdeptask FROM task_recdeptask WHERE task=?",
            (self.id,)))

    def get_recrdeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT recrdeptask FROM task_recrdeptask WHERE task=?",
            (self.id,)))

    def get_recadeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT recadeptask FROM task_recadeptask WHERE task=?",
            (self.id,)))

    def get_taskdepends(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT parent_item, parent_task FROM task_depend WHERE task=?",
            (self.id,)))


    def stampfile_path(self):
        try:
            return self._stampfile
        except AttributeError:
            stampdir = self.recipe.get("STAMPDIR")
            self._stampfile = (stampdir, os.path.join(stampdir, self.name))
        return self._stampfile


    # return (mtime, hash) from stamp file
    def read_stamp(self):
        stampfile = self.stampfile_path()[1]
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


    def build_started(self):
        if self.nostamp:
            return
        (stampdir, stampfile) = self.stampfile_path()
        if not os.path.exists(stampdir):
            os.makedirs(stampdir)
        open(stampfile, "w").close()
        return


    def build_done(self, buildhash):
        if self.nostamp:
            return
        (stampdir, stampfile) = self.stampfile_path()
        if not os.path.exists(stampdir):
            os.makedirs(stampdir)
        with open(stampfile, "w") as _stampfile:
            _stampfile.write(buildhash)
        return


    def build_failed(self):
        return


    def task_cleaned(self):
        hashpath = self.stampfile_path()[1]
        if os.path.exists(hashpath):
            os.remove(hashpath)


    def prepare_meta(self, runq):
        if self.meta is not None:
            return self.meta

        meta = self.recipe.meta.copy()

        buildhash = self.cookbook.baker.runq.get_buildhash(self)
        debug("buildhash=%s"%(repr(buildhash)))
        meta.setVar("TASK_BUILDHASH", buildhash)

        recipe_type = meta.get("RECIPE_TYPE")

        def prepare_stage(get_depend_packages):
            stage = {}
            recdepends = []
            get_package_filename = self.cookbook.baker.runq.get_package_filename
            packages = get_depend_packages(self) or []
            for package in packages:
                package = self.cookbook.get_package(id=package)
                filename = get_package_filename(package)
                if not filename in stage:
                    stage[filename] = package
            return stage

        meta["__stage"] = prepare_stage(
            self.cookbook.baker.runq.get_depend_packages)
        meta["__rstage"] = prepare_stage(
            self.cookbook.baker.runq.get_rdepend_packages)
        meta.set_flag("__stage", "nohash", True)
        meta.set_flag("__rstage", "nohash", True)

        # Filter meta-data, enforcing restrictions on which tasks to
        # emit vars to and not including other task functions.
        for var in meta:
            emit_flag = meta.get_flag(var, "emit")
            emit = (emit_flag or "").split()
            taskfunc_match = self.TASKFUNC_RE.match(var)
            if taskfunc_match:
                if taskfunc_match.group(0) not in emit:
                    emit.append(taskfunc_match.group(0))
            if (emit or emit_flag == "") and not self.name in emit:
                del meta[var]
                continue
            omit = meta.get_flag(var, "omit")
            if omit is not None and self.name in omit.split():
                del meta[var]
                continue

        self.meta = meta
        return meta


    def run(self):
        assert self.meta is not None
        function = self.meta.get_function(self.name)

        self.do_cleandirs()
        cwd = self.do_dirs() or self.meta.get("B")

        # Setup stdin, stdout and stderr redirection
        stdin = open("/dev/null", "r")
        logfn = "%s/%s.%s.log"%(function.tmpdir, self.name, str(os.getpid()))
        logsymlink = "%s/%s.log"%(function.tmpdir, self.name)
        bb.utils.mkdirhier(os.path.dirname(logfn))
        try:
            if oebakery.DEBUG:
                logfile = os.popen("tee %s"%logfn, "w")
            else:
                logfile = open(logfn, "w")
        except OSError:
            print "Opening log file failed: %s"%(logfn)
            raise

        if os.path.exists(logsymlink) or os.path.islink(logsymlink):
            os.remove(logsymlink)
        os.symlink(logfn, logsymlink)

        real_stdin = os.dup(sys.stdin.fileno())
        real_stdout = os.dup(sys.stdout.fileno())
        real_stderr = os.dup(sys.stderr.fileno())
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(logfile.fileno(), sys.stdout.fileno())
        os.dup2(logfile.fileno(), sys.stderr.fileno())

        try:
            for prefunc in self.get_prefuncs():
                print "running prefunc", prefunc
                self.do_cleandirs(prefunc)
                wd = self.do_dirs(prefunc)
                if not prefunc.run(wd or cwd):
                    return False
            try:
                if not function.run(cwd):
                    return False
            except oebakery.FatalError:
                return False
            for postfunc in self.get_postfuncs():
                print "running postfunc", postfunc
                self.do_cleandirs(postfunc)
                wd = self.do_dirs(postfunc)
                if not postfunc.run(wd or cwd):
                    return False
            return True

        finally:
            # Cleanup stdin, stdout and stderr redirection
            os.dup2(real_stdin, sys.stdin.fileno())
            os.dup2(real_stdout, sys.stdout.fileno())
            os.dup2(real_stderr, sys.stderr.fileno())
            stdin.close()
            logfile.close()
            os.close(real_stdin)
            os.close(real_stdout)
            os.close(real_stderr)
            if os.path.exists(logfn) and os.path.getsize(logfn) == 0:
                os.remove(logsymlink)
                os.remove(logfn) # prune empty logfiles


    def do_cleandirs(self, name=None):
        if not name:
            name = self.name
        cleandirs = (self.meta.get_flag(name, "cleandirs",
                                        oelite.meta.FULL_EXPANSION))
        if cleandirs:
            for cleandir in cleandirs.split():
                if not os.path.exists(cleandir):
                    continue
                try:
                    #print "cleandir %s"%(cleandir)
                    shutil.rmtree(cleandir)
                except Exception, e:
                    err("cleandir %s failed: %s"%(cleandir, e))
                    raise

    def do_dirs(self, name=None):
        if not name:
            name = self.name
        # Create directories and find directory to execute in
        dirs = (self.meta.get_flag(name, "dirs",
                                   oelite.meta.FULL_EXPANSION))
        if dirs:
            dirs = dirs.split()
            for dir in dirs:
                bb.utils.mkdirhier(dir)
            return dir

    def get_postfuncs(self):
        postfuncs = []
        for name in (self.meta.get_flag(self.name, "postfuncs", 1)
                     or "").split():
            postfuncs.append(self.meta.get_function(name))
        return postfuncs

    def get_prefuncs(self):
        prefuncs = []
        for name in (self.meta.get_flag(self.name, "prefuncs", 1)
                     or "").split():
            prefuncs.append(self.meta.get_function(name))
        return prefuncs
