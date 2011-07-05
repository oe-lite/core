import oelite
from oelite.meta import *
import bb.utils
import os


def inlineeval(source, meta):
    g = meta.get_pythonfunc_globals()
    try:
        return eval(source, g, {"d": meta})
    except Exception:
        print "Exception while evaluating inline python code"
        #print "Exception while evaluating inline python code: %s"%(repr(source))
        raise


def exechooks(meta, name, hooks=None):
    if hooks is None:
        hooks = meta.get_hooks(name)
    tmpdir = os.path.join(meta.get("HOOKTMPDIR"), name)
    bb.utils.mkdirhier(tmpdir)
    for function in hooks:
        pn = meta.get("PN")
        if pn:
            name = "%s.%s.%s"%(pn, meta.get("RECIPE_TYPE"), function)
        else:
            name = function
        hook = meta.get_pythonfunc(function, name, tmpdir=tmpdir,
                                   set_ld_library_path=False)
        retval = hook.run(tmpdir)
        if retval is not None and not retval:
            raise oelite.HookFailed(name, function, retval)
    return
