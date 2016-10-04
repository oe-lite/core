import oelite.meta
import oebakery
import bb

import sys
import os
import shutil
import warnings
import re
import subprocess

class OEliteFunction(object):

    def __init__(self, meta, var, name=None, tmpdir=None):
        self.meta = meta
        self.var = var
        if name:
            self.name = name
        else:
            self.name = var
        if tmpdir:
            self.tmpdir = tmpdir
        else:
            self.tmpdir = self.meta.get("T")
            if not self.tmpdir:
                die("T variable not set, unable to build")
        return

    def __str__(self):
        return "%s"%(self.var)

    def __repr__(self):
        return "OEliteFunction(%s)"%(self.var)

    def run(self, cwd):
        self.start(cwd)
        return self.wait(False)

    def start(self, cwd):
        # Change directory
        old_cwd = os.getcwd()
        os.chdir(cwd)
        # Fixup umask
        umask = self.meta.get_flag(self.var, "umask")
        if umask is not None:
            umask = int(umask, 8)
        else:
            umask = int(self.meta.get("DEFAULT_UMASK"), 8)
        old_umask = os.umask(umask)
        try:
            self._start()
        finally:
            # Restore directory
            os.chdir(old_cwd)
            # Restore umask
            os.umask(old_umask)

    def _start(self):
        self.result = self()

    def wait(self, poll=False):
        return self.result


class NoopFunction(OEliteFunction):

    def start(self, cwd):
        self.result = True


class PythonFunction(OEliteFunction):

    def __init__(self, meta, var, name=None, tmpdir=None, recursion_path=None,
                 set_os_environ=True):
        # Don't put the empty list directly in the function definition
        # as default arguments, as modifications of this "empty" list
        # will be done in-place so that it will not be truly empty
        # next time
        if recursion_path is None:
            recursion_path = []
        recursion_path.append(var)
        funcimports = {}
        for func in (meta.get_flag(var, "import",
                                   oelite.meta.FULL_EXPANSION)
                     or "").split():
            #print "importing func", func
            if func in funcimports:
                continue
            if func in recursion_path:
                raise Exception("circular import %s -> %s"%(recursion_path, func))
            python_function = PythonFunction(meta, func, tmpdir=tmpdir,
                                             recursion_path=recursion_path)
            funcimports[func] = python_function.function
        g = meta.get_pythonfunc_globals()
        g.update(funcimports)
        l = {}
        self.code = meta.get_pythonfunc_code(var)
        eval(self.code, g, l)
        self.function = l[var]
        self.set_os_environ = set_os_environ
        self.result = False
        super(PythonFunction, self).__init__(meta, var, name, tmpdir)
        return

    def __call__(self):

        if self.set_os_environ:
            for var in self.meta.get_vars(flag="export", values=True):
                if self.meta.get_flag(var, "unexport"):
                    continue
                val = self.meta.get(var)
                if val is None:
                    val = ""
                if var == "LD_LIBRARY_PATH":
                    var = (self.meta.get("LD_LIBRARY_PATH_VAR")
                           or "LD_LIBRARY_PATH")
                os.environ[var] = val
        try:
            retval = self.function(self.meta)
        finally:
            os.environ.clear()
        if isinstance(retval, basestring):
            return retval or True
        if retval is None:
            return True
        return bool(retval)


class ShellFunction(OEliteFunction):

    def __init__(self, meta, var, name=None, tmpdir=None):
        self.result = None
        super(ShellFunction, self).__init__(meta, var, name, tmpdir)
        return

    def wait(self, poll):
        if self.result is not None:
            return self.result
        if poll:
            ret = self.subprocess.poll()
        else:
            ret = self.subprocess.wait()
        if ret is None:
            return None
        if ret == 0:
            self.result = True
        else:
            self.result = False
            print "Error: Command failed: %r: %d"%(self.cmdstr, ret)
        return self.result


    def startscript(self, cmd):
        self.cmdstr = cmd
        cmdname = cmd.split(None, 1)[0]

        print '> %s'%(cmd,)

        try:
            self.subprocess = subprocess.Popen(cmd, stdin=sys.stdin, shell=True)
        except OSError, e:
            if e.errno == 2:
                print "Error: Command not found:", cmdname
            else:
                print "Error: Command failed: %r"%(cmd)
            self.result = False

    def _start(self):
        runfn = "%s/%s.%s.run" % (self.tmpdir, self.name, self.meta.get("DATETIME"))
        runsymlink = "%s/%s.run" % (self.tmpdir, self.name)

        body = self.meta.get(self.name)
        if not body:
            return True

        runfile = open(runfn, "w")
        runfile.write("#!/bin/bash -e\n\n")
        if os.path.exists(runsymlink) or os.path.islink(runsymlink):
            os.remove(runsymlink)
        os.symlink(os.path.basename(runfn), runsymlink)

        vars = self.meta.keys()
        vars.sort()
        bashfuncs = []
        for var in vars:
            if self.meta.get_flag(var, "python"):
                continue
            if "-" in var:
                bb.warn("cannot emit var with '-' to bash:", var)
                continue
            if self.meta.get_flag(var, "unexport"):
                continue
            val = self.meta.get(var)
            if self.meta.get_flag(var, "bash"):
                bashfuncs.append((var, val))
                continue
            if self.meta.get_flag(var, "export"):
                runfile.write("export ")
            if val is None:
                val = ""
            if not isinstance(val, basestring):
                #print "ignoring var %s type=%s"%(var, type(val))
                continue
            quotedval = re.sub('"', '\\"', val or "")
            if var == "LD_LIBRARY_PATH":
                var = (self.meta.get("LD_LIBRARY_PATH_VAR")
                       or "LD_LIBRARY_PATH")
            runfile.write('%s="%s"\n'%(var, quotedval))
        for (var, val) in bashfuncs:
            runfile.write("\n%s() {\n%s\n}\n"%(
                    var, (val or "\t:").rstrip()))

        runfile.write("set -x\n")
        runfile.write("cd %s\n"%(os.getcwd()))
        runfile.write("%s\n"%(self.name))
        runfile.close()
        os.chmod(runfn, 0755)
        cmd = "%s"%(runfn)
        if self.meta.get_flag(self.name, "fakeroot"):
            cmd = "%s "%(self.meta.get("FAKEROOT") or "fakeroot") + cmd
        cmd = "LC_ALL=C " + cmd
        return self.startscript(cmd)
