import oebakery
from oebakery import die, err, warn, info, debug
import oelite.data
import sys, string

builtin_nohash = [
    "OE_REMOTES",
    "OE_MODULES",
    "BB_ENV_WHITELIST",
    "PATH",
    "PWD",
    "SHELL",
    "TERM",
    "TOPDIR",
    "TMPDIR",
    "BBPATH",
    "BBPATH_PRETTY",
    "BBFILES",
    "BBFILES_PRETTY",
    "BBRECIPES",
    "FILE",
]

builtin_nohash_prefix = [
    "OE_REMOTE_",
    "OE_MODULE_",
]

def dump_var(key, o=sys.__stdout__, d=bb.data.init(), pretty=True,
             topdir=None, workdir=None):
    if pretty:
        eol = "\n\n"
    else:
        eol = "\n"

    val = d.getVar(key, True)

    if not val:
        return 0

    val = str(val)

    if workdir:
        val = string.replace(val, workdir, "${WORKDIR}")
    if topdir:
        val = string.replace(val, topdir, "${TOPDIR}")

    if d.getVarFlag(key, "func"):
        o.write("%s() {\n%s}%s"%(key, val, eol))
        return

    if pretty:
        o.write("# %s=%s\n"%(key, d.getVar(key, False)))
    if d.getVarFlag(key, "export"):
        o.write("export ")
    
    o.write("%s=%s%s"%(key, repr(val), eol))
    return

def dump(o=sys.__stdout__, d=bb.data.init(), pretty=True, nohash=False):

    topdir = d.getVar("TOPDIR", True)
    workdir = d.getVar("WORKDIR", True)

    keys = sorted((key for key in d.keys() if not key.startswith("__")))
    for key in keys:
        if not nohash:
            if key in builtin_nohash:
                continue
            if d.getVarFlag(key, "nohash"):
                continue
            for prefix in builtin_nohash_prefix:
                if key.startswith(prefix):
                    continue
        dump_var(key, o, d, pretty, topdir, workdir)
