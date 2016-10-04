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

trace_entries = []
def flush_trace_entries():
    if profiledir is None:
        return
    with profile_output("trace.txt", "a") as f:
        for e in trace_entries:
            f.write(e[0])
            if (e[1] > 1):
                f.write(" {%d times}" % e[1])
            f.write("\n")
    del trace_entries[:]

def trace(payload = "", depth = 3):
    import inspect

    txt = ""
    stack = inspect.stack()
    for i in range(depth, 0, -1):
        try:
            frame = stack[i]
            fn = os.path.basename(frame[1])
            line = frame[2]
            func = frame[3]
            if txt:
                txt += " -> "
            txt += "%s:%d:%s()" % (fn, line, func)
        except IndexError:
            pass
    if payload:
        txt += ": " + payload
    if trace_entries and trace_entries[-1][0] == txt:
        trace_entries[-1][1] += 1
    else:
        e = [txt, 1]
        trace_entries.append(e)
        if len(trace_entries) > 10000:
            flush_trace_entries()

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
    collect = {}
    for f in profiled_functions:
        name = f.__name__
        try:
            srcfile = inspect.getsourcefile(f)
        except TypeError:
            srcfile = "<unknown>"
        try:
            lineno = str(inspect.getsourcelines(f)[1])
        except:
            lineno = "?"
        t = (srcfile, lineno, name)
        if not t in collect:
            collect[t] = SimpleStats()
        collect[t].update(profiled_functions[f])
    with profile_output("call_stats.txt") as out:
        for (srcfile, lineno, name), stats in sorted(collect.iteritems()):
            srcfile = os.path.basename(srcfile)
            stats.compute()
            out.write("%-12s\t%-24s\t%9.3fs / %5d = %7.3f " %
                    (srcfile + ":" + lineno, name,
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
    atexit.register(flush_trace_entries)

class SimpleStats:
    def __init__(self):
        self.data = []

    def __iter__(self):
        return iter(self.data)

    def append(self, val):
        self.data.append(val)

    def update(self, other):
        self.data.extend(other)

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

def do_memdump():
    try:
        from meliae import scanner
    except ImportError:
        sys.stderr.write("meliae module unavailable\n")
        return
    import gc
    # to get more accurate and comparable results, do a full garbage
    # collection before dumping.
    gc.collect()
    with profile_output("meliae.json") as f:
        scanner.dump_all_objects(f)

def do_dict_stat(small_limit = 4):
    try:
        from meliae import scanner
    except ImportError:
        sys.stderr.write("meliae module unavailable\n")
        return
    import gc
    # to get more accurate and comparable results, do a full garbage
    # collection before dumping.
    gc.collect()
    small_dict_keys = dict()
    dict_sizes = dict()
    for ob in scanner.get_recursive_items(gc.get_objects()):
        if not isinstance(ob, dict):
            continue
        if ob is small_dict_keys:
            continue
        l = len(ob)
        if l in dict_sizes:
            dict_sizes[l] += 1
        else:
            dict_sizes[l] = 1
        if l >= small_limit:
            continue
        t = tuple(sorted(ob.keys()))
        if t in small_dict_keys:
            small_dict_keys[t] += 1
        else:
            small_dict_keys[t] = 1
    with profile_output("small_dict_keys.txt") as f:
        for t in sorted(small_dict_keys.keys(), key=lambda t: (len(t),small_dict_keys[t])+t):
            if small_dict_keys[t] > 1:
                f.write("%s\t%d\n" % (repr(t), small_dict_keys[t]))
    with profile_output("dict_sizes.txt") as f:
        for t in sorted(dict_sizes.keys()):
            f.write("%d\t%d\n" % (t, dict_sizes[t]))
