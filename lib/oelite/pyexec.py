def inlineeval(source, meta):
    g = meta.get_pythonfunc_globals()
    g.update(meta.get_autoimport_pythonfuncs(g))
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
        #print "%s hook %s"%(name, function)
        g = meta.get_pythonfunc_globals()
        #g["d"] = meta
        g.update(meta.get_autoimport_pythonfuncs(g))
        hook = meta.get_pythonfunc(function, g)

        #funcimports = meta.get_pythonfuncs(
        #    (meta.getVarFlag(function, "funcimport", expand=1) or "").split())
        #funcimports.update(meta.get_autoimport_pythonfuncs())
        #funcimports.update(meta.get_pythonfuncs([function]))

        #args = meta.getVarFlag(function, "args") or ""
        #source = ("def %s(%s):\n"%(function, args) +
        #          meta.getVar(function, expand=0) + "\n")
        #(g, l) = execlite(source, meta, funcimports, "%s"%(function))
        #retval = eval("%s()"%(function))
        #print "funcimports = %s"%(funcimports.keys())

        #retval = evallite("%s()\n"%(function), meta, funcimports)

        retval = hook(meta)

        #print "stopping after running first hook: retval=%s"%(repr(retval))
        #import sys
        #sys.exit(42)



#__pyexec_precompile_cache__ = {}
#
#def precompile(name, source):
#    global __pyexec_precompile_cache__
#    if not name in __pyexec_precompile_cache__:
#        code = compile(source, name, "exec")
#        __pyexec_precompile_cache__[name] = code
#        return


#def import_modules(imports, c={}):
#    print "imports=%s"%(imports)
#    for name in imports.split():
#        print "importing", name
#        base = name.split(".")[0]
#        c[base] = __import__(name, c, [], [], 0)
#        #cmd = __import__(name)
#        #print dir(hest)
#        #c[name] = __builtins__["eval"](name)
#    return c


#def evallite(source, data, functions=None):
#    g = pythonfunc_globals(data)
#    if functions:
#        l = functions.copy()
#        #l["d"] = data
#    else:
#        #l = {"d": data}
#        l = {}
#    return eval(source, g, l)


#def execlite(source, data, functions=None, funcname="<unknown function>"):
#    g = pythonfunc_globals(data)
#    if functions:
#        l = functions.copy()
#        #l["d"] = data
#    else:
#        #l = {"d": data}
#        l = {}
#    code = compile(source, "<%s>"%(funcname), "exec")
#    try:
#        eval(code, g, l)
#    except Exception, e:
#        print "Error while executing python function %s: %s"%(funcname, e)
#        print
#        import traceback
#        traceback.print_exc()
#        print
#        raise
#    return (g, l)


#__pyexec_globals__ = {}
#
#def pythonfunc_globals(data, imports=None):
#    if imports is None:
#        imports = (data.getVar("OE_IMPORTS", expand=0) or "")
#        print "OE_IMPORTS=%s"%(imports)
#    global __pyexec_globals__
#    try:
#        g = __pyexec_globals__[imports]
#    except KeyError:
#        g = __pyexec_globals__[imports] = {}
#        g["__builtins__"] = globals()["__builtins__"]
#        for module_name in imports.split():
#            print "importing module", module_name
#            base_name = module_name.split(".")[0]
#            g[base_name] = __import__(module_name, g, [], [], 0)
#    #return g.copy()
#    g = g.copy()
#    g.update({"d": data})
#    return g
