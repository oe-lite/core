import time
import functools
import atexit
import oelite.util
import inspect
import os
import sys
import subprocess
from resource import *

now = time.time

profiledir = None

def profile_output(name, mode="a"):
    if profiledir:
        path = os.path.join(profiledir, name)
    else:
        path = "/dev/null"
    return open(path, mode)

# Decorating any function with @profile_calls will record the duration
# of every call of that function. Some statistics on these are
# automatically printed to $profiledir/callstats.txt on exit.
profiled_functions = dict()
def profile_calls(somefunc):
    @functools.wraps(somefunc)
    def recordtime(*args, **kwargs):
        start = now()
        try:
            return somefunc(*args, **kwargs)
        finally:
            delta = now()-start
            if not somefunc in profiled_functions:
                profiled_functions[somefunc] = SimpleStats()
            profiled_functions[somefunc].append(delta)
    return recordtime

def write_call_stats():
    with profile_output("call_stats.txt") as out:
        for f in sorted(profiled_functions.keys(), key=lambda x: x.__name__):
            name = f.__name__
            try:
                srcfile = os.path.basename(inspect.getsourcefile(f))
            except TypeError:
                srcfile = "<unknown>"

            stats = profiled_functions[f]
            stats.compute()
            out.write("%-12s\t%-24s\t%9.3fs / %5d = %7.3f " %
                    (srcfile, f.__name__,
                     stats.sum, stats.count, stats.mean))
            out.write("[%s]\n" % ", ".join(["%7.3f" % x for x in stats.quartiles]))

# For detailed profiling of individual phases (recipe parsing, hash
# computation, entire build, ...) - records memory information as well
# as wallclock, user and system times.
class Rusage:
    rusage_names = [
        ("wtime",     "wallclock time", "%7.3f"),
        ("ru_stime",  "system time   ", "%7.3f"),
        ("ru_utime",  "user time     ", "%7.3f"),
        ("ru_minflt", "minor faults  ", "%7d"),
        ("ru_majflt", "major faults  ", "%7d"),
        ("ru_maxrss", "max RSS       ", "%7d KiB"),
        ("ru_nvcsw",  "context switches, voluntary  ", "%7d"),
        ("ru_nivcsw", "context switches, involuntary", "%7d"),
    ]
    # For recording deltas before profiledir is created
    deferred = []

    def compute_delta(self):
        delta = dict()
        for m,_,_ in Rusage.rusage_names:
            delta[m] = self.after[m] - self.before[m]
        self.delta = delta

    @classmethod
    def current_rusage(self):
        # Reading /proc/self/status, in particular the VmPeak and
        # VmSize fields, may also be interesting.
        x = getrusage(RUSAGE_SELF)
        y = dict([(m, getattr(x, m)) for m,_,_ in self.rusage_names if m.startswith("ru_")])
        y["wtime"] = now()
        return y

    def print_delta(self):
        with profile_output("rusage_delta.txt") as f:
            f.write("%s:\n" % self.name)
            for key, name, fmt in self.rusage_names:
                f.write(("  %s " + fmt + "\n") % (name, self.delta[key]))
            f.write("\n")

    @classmethod
    def print_deferred(self):
        for p in self.deferred:
            p.print_delta()

    def __init__(self, name, print_walltime=True):
        self.name = name
        self.start()
        self.print_walltime = print_walltime

    def start(self):
        self.before = self.current_rusage()
        oelite.util.stracehack("start:" + self.name)

    def end(self):
        oelite.util.stracehack("end:" + self.name)
        self.after = self.current_rusage()
        self.compute_delta()

        if profiledir:
            self.print_delta()
        else:
            Rusage.deferred.append(self)
        if self.print_walltime:
            print "%s: %s" % (self.name, oelite.util.pretty_time(self.delta['wtime']))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.end()

# For easy automatic 10000 foot profiling of run-once (or run rarely)
# functions, just decorate it with
#
# @oelite.profiling.profile_rusage_delta
def profile_rusage_delta(somefunc):
    @functools.wraps(somefunc)
    def recorddelta(*args, **kwargs):
        name = somefunc.__name__
        try:
            srcfile = os.path.basename(inspect.getsourcefile(somefunc))
        except TypeError:
            srcfile = "<unknown>"
        try:
            lineno = str(inspect.getsourcelines(somefunc)[1])
        except:
            lineno = "?"
        with Rusage("%s:%s:%s" % (srcfile, lineno, name), print_walltime=False):
            return somefunc(*args, **kwargs)
    return recorddelta

def write_basic_info(config):
    with profile_output("info.txt") as f:
        f.write("argv: %s\n" % " ".join(sys.argv))
        f.write("PARALLEL_MAKE: %s\n" % (config.get("PARALLEL_MAKE") or ""))
        for layer in (config.get("OESTACK") or "").split():
            layer = layer.split(";")[0]
            cmd = "cd %s && git describe --long --dirty --abbrev=10 --tags --always" % layer
            try:
                desc = subprocess.check_output(cmd, shell=True)
            except subprocess.CalledProcessError:
                desc = "unknown\n"
            f.write("%s: %s" % (layer, desc))

def init(config):
    global profiledir
    profiledir = os.path.join(config.get("TMPDIR"), "profiling", config.get("DATETIME"))
    oelite.util.makedirs(profiledir)
    linkpath = os.path.join(config.get("TMPDIR"), "profiling", "latest")
    try:
        os.unlink(linkpath)
    except OSError:
        pass
    os.symlink(config.get("DATETIME"), linkpath)

    write_basic_info(config)
    Rusage.print_deferred()

    atexit.register(write_call_stats)

class SimpleStats:
    def __init__(self):
        self.data = []

    def append(self, val):
        self.data.append(val)

    def compute(self):
        self.data.sort()
        self.sum = sum(self.data)
        self.count = len(self.data)
        try:
            self.mean = self.sum / len(self.data)
        except ZeroDivisionError:
            self.mean = float('nan')
        self.quartiles = [self.percentile(p) for p in (0,25,50,75,100)]

    def percentile(self, p):
        if len(self.data) == 0:
            return float('nan')
        elif len(self.data) == 1:
            return self.data[0]
        p = float(p)
        if p < 0.0 or p > 100.0:
            raise ValueError("p outside valid range")
        p /= 100.0
        p *= len(self.data)-1
        i = int(p)
        if i == len(self.data)-1:
            return self.data[-1]
        return (p-i)*(self.data[i+1]-self.data[i]) + self.data[i]
