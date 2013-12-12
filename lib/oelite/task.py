import oebakery
from oebakery import die, err, warn, info, debug
import oelite.meta
import oelite.recipe
from oelite.dbutil import *
import oelite.function
import oelite.util
import oelite.process
import oelite.log

import sys
import os
import warnings
import shutil
import re
import cPickle

log = oelite.log.get_logger()

def task_name(name):
    if name.startswith("do_"):
        return name
    return "do_" + name


class OEliteTask(object):

    def __init__(self, id, recipe, name, nostamp, cookbook):
        self.id = id
        self.recipe = cookbook.get_recipe(id=recipe)
        self.name = name
        self.nostamp = nostamp
        self.cookbook = cookbook
        self.debug = self.cookbook.debug
        return

    def __str__(self):
        return "%s:%s"%(self.recipe, self.name)

    def save(self, file, token):
        cPickle.dump(self.signature, file, 2)
        self.meta.pickle(file)

    def load_summary(self, file):
        self.signature = cPickle.load(file)
        return

    def load_meta(self, file=None):
        if file is None:
            # self.meta_cache can be gotten from MetaCache.task_cache
            # but do we have a MetaCache object here?
            cache = self.recipe.get_cache()
            file = open(cache.task_cache(self), 'r')
            file.seek(self.meta_cache_offset)
        self.meta = oelite.meta.dict.unpickle(file)
        return

    def get_parents(self):
        parents = flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT parent FROM task_parent WHERE recipe=? AND task=?",
            (self.recipe.id, self.name,)))
        if not parents:
            return []
        return self.cookbook.get_tasks(recipe=self.recipe, name=parents)

    def get_deptasks(self, deptypes):
        assert isinstance(deptypes, list) and len(deptypes) > 0
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT deptask FROM task_deptask "
            "WHERE deptype IN (%s) "%(",".join("?" for i in deptypes)) +
            "AND task=?", deptypes + [self.id]))

    def get_recdeptasks(self, deptypes):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT recdeptask FROM task_recdeptask "
            "WHERE deptype IN (%s) "%(",".join("?" for i in deptypes)) +
            "AND task=?", deptypes + [self.id]))

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

    def prepare(self, runq):
        buildhash = self.cookbook.baker.runq.get_task_buildhash(self)
        debug("buildhash=%s"%(repr(buildhash)))
        self.meta.set("TASK_BUILDHASH", buildhash)

        def prepare_stage(deptype):
            stage = {}
            recdepends = []
            get_package_filename = self.cookbook.baker.runq.get_package_filename
            packages = self.cookbook.baker.runq.get_depend_packages(
                self, deptype) or []
            for package in packages:
                package = self.cookbook.get_package(id=package)
                filename = get_package_filename(package)
                if not filename in stage:
                    stage[filename] = package
            return stage

        self.meta["__stage"] = prepare_stage("DEPENDS")
        self.meta["__rstage"] = prepare_stage("RDEPENDS")
        self.meta["__fstage"] = prepare_stage("FDEPENDS")
        self.meta.set_flag("__stage", "nohash", True)
        self.meta.set_flag("__rstage", "nohash", True)
        self.meta.set_flag("__fstage", "nohash", True)

        return




    def run(self):
        meta = self.meta
        function = meta.get_function(self.name)

        self.do_cleandirs()
        cwd = self.do_dirs() or meta.get("B")

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
                    if os.path.islink(cleandir):
                        os.unlink(cleandir)
                    else:
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
                oelite.util.makedirs(dir)
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


# refactor of Task.meta method

class MetaProcessor(oelite.process.PythonProcess):

    TASKFUNC_RE = re.compile(r"^do_([a-z]+).*?")

    def __init__(self, task, process=False):
        if process:
            self.meta = task.recipe.meta
        else:
            self.meta = task.recipe.meta.copy()
        self.cache = task.recipe.get_cache()
        self.task = task
        tmpfile = os.path.join(
            task.recipe.cookbook.config.get('PARSERDIR'),
            oelite.path.relpath(task.recipe.filename)
            + '.%s.%s'%(task.recipe.type, task.name))
        stdout = tmpfile + '.log'
        ipc = tmpfile + '.ipc'
        super(MetaProcessor, self).__init__(
            stdout=stdout, ipc=ipc, target=self._prepare)
        return

    def _prepare(self):
        retval = self.prepare()
        if not hasattr(self, 'feedback'):
            return retval
        if retval:
            self.feedback.error("Task metadata processing failed: %s"%(retval))
            assert isinstance(retval, int)
            sys.exit(retval)
        else:
            self.feedback.progress(100)
            sys.exit(0)

    def prepare(self):
        log.debug("Preparing %s", self.task)
        # Filter meta-data, enforcing restrictions on which tasks to
        # emit vars to and not including other task functions.
        emit_prefixes = (self.meta.get("META_EMIT_PREFIX") or "").split()
        def colon_split(s):
            import string
            return string.split(s, ":", 1)
        emit_prefixes = map(colon_split, emit_prefixes)
        for var in self.meta.keys():
            emit_flag = self.meta.get_flag(var, "emit")
            emit = (emit_flag or "").split()
            taskfunc_match = self.TASKFUNC_RE.match(var)
            if taskfunc_match:
                if taskfunc_match.group(0) not in emit:
                    emit.append(taskfunc_match.group(0))
            for emit_task, emit_prefix in emit_prefixes:
                if not var.startswith(emit_prefix):
                    continue
                if emit_task == "":
                    if emit_flag is None:
                        emit_flag = ""
                    continue
                if not emit_task.startswith("do_"):
                    emit_task = "do_" + emit_task
                if not emit_task in emit:
                    emit.append(emit_task)
            if (emit or emit_flag == "") and not self.task.name in emit:
                del self.meta[var]
                continue
            omit = self.meta.get_flag(var, "omit")
            if omit is not None and self.task.name in omit.split():
                del self.meta[var]
                continue

        # FIXME: add options.dump_signature_metadata support back here
        #if self.options.dump_signature_metadata:
        #    self.normpath(task.recipe.filename)
        #    dump = os.path.join(self.options.dump_signature_metadata,
        #                        self.normpath(task.recipe.filename),
        #                        str(task))
        #else:
        #    dump = None

        try:
            signature = self.meta.signature() # (dump=dump)
        except oelite.meta.ExpansionError as e:
            e.msg += " in %s"%(self.task)
            e.print_details()
            #raise
            return 1

        self.task.meta = self.meta
        self.task.signature = signature

        # FIXME: save to cache
        self.cache.save_task(self.task)

        return
