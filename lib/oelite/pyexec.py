import oelite
import oelite.util
from oelite.function import PythonFunction
from oelite.meta import *
import os


def inlineeval(source, meta, var=None):
    g = meta.get_pythonfunc_globals()
    if var:
        recursion_path = []
        funcimports = {}
        for func in (meta.get_flag(var, "import",
                                   oelite.meta.FULL_EXPANSION)
                     or "").split():
            if func in funcimports:
                continue
            if func in recursion_path:
                raise Exception("circular import %s -> %s"%(recursion_path, func))
            python_function = PythonFunction(meta, func,
                                             recursion_path=recursion_path)
            funcimports[func] = python_function.function
        g.update(funcimports)
    try:
        return eval(source, g, {"d": meta})
    except Exception:
        print "Exception while evaluating inline python code"
        #print "Exception while evaluating inline python code: %s"%(repr(source))
        raise


def exechooks(meta, hookname, remove_hooks=True):
    hooks = meta.get_hooks(hookname)
    tmpdir = os.path.join(meta.get("HOOKTMPDIR"), hookname)
    oelite.util.makedirs(tmpdir)
    for function in hooks:
        pn = meta.get("PN")
        if pn:
            name = "%s.%s.%s"%(pn, meta.get("RECIPE_TYPE"), function)
        else:
            name = function
        hook = meta.get_pythonfunc(function, name, tmpdir=tmpdir,
                                   set_os_environ=False)
        retval = hook.run(tmpdir)
        if isinstance(retval, basestring):
            raise oelite.HookFailed(name, function, retval)
        elif not retval:
            raise oelite.HookFailed(name, function, retval)
    if remove_hooks:
        meta.del_hooks(hookname)
    return
