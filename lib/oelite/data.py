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
    "_task_deps",
]

builtin_nohash_prefix = [
    "OE_REMOTE_",
    "OE_MODULE_",
]

def dump_var(key, o=sys.__stdout__, d=bb.data.init(), pretty=True,
             dynvars = {}):
    if pretty:
        eol = "\n\n"
    else:
        eol = "\n"

    val = d.getVar(key, True)

    if not val:
        return 0

    val = str(val)

    for varname in dynvars.keys():
        val = string.replace(val, dynvars[varname], "${%s}"%(varname))

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

    dynvars = {}
    for varname in ("WORKDIR", "TOPDIR", "DATETIME"):
        dynvars[varname] = d.getVar(varname, True) or None

    keys = sorted((key for key in d.keys() if not key.startswith("__")))
    for key in keys:
        if not nohash:
            if key in builtin_nohash:
                continue
            if d.getVarFlag(key, "nohash"):
                continue
            nohash_prefixed = False
            for prefix in builtin_nohash_prefix:
                if key.startswith(prefix):
                    nohash_prefixed = True
                    break
            if nohash_prefixed:
                continue
        dump_var(key, o, d, pretty, dynvars)
