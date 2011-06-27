import oelite
from oelite.meta import *

class PythonFunction:

    def __init__(self, meta, var, recursion_path=[]):
        recursion_path.append(var)
        funcimports = {}
        for func in (meta.get_flag(var, "funcimport", FULL_EXPANSION)
                     or "").split():
            if func in funcimports:
                continue
            if func in recursion_path:
                raise Exception("circular funcimport")
            python_function = PythonFunction(func, g, recursion_path)
            funcimports[func] = python_function.function
        g = meta.get_pythonfunc_globals()
        g.update(funcimports)
        l = {}
        self.code = meta.get_pythonfunc_code(var)
        eval(self.code, g, l)
        self.function = l[var]
        return

    def run(self, meta):
        return self.function(meta)


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
    for function in hooks:
        hook = meta.get_pythonfunc(function)
        retval = hook.run(meta)
        if retval is not None:
            raise oelite.HookFailed(name, function, retval)
