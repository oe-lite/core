def inlineeval(source, data):
    g = data.get_pythonfunc_globals()
    g.update(data.get_autoimport_pythonfuncs(g))
    return eval(source, g, {"d": data})


def exechooks(data, name, hooks=None):
    if hooks is None:
        hooks = data.get_hooks(name)
    for function in hooks:
        #print "%s hook %s"%(name, function)
        g = data.get_pythonfunc_globals()
        #g["d"] = data
        g.update(data.get_autoimport_pythonfuncs(g))
        hook = data.get_pythonfunc(function, g)

        #funcimports = data.get_pythonfuncs(
        #    (data.getVarFlag(function, "funcimport", expand=1) or "").split())
        #funcimports.update(data.get_autoimport_pythonfuncs())
        #funcimports.update(data.get_pythonfuncs([function]))

        #args = data.getVarFlag(function, "args") or ""
        #source = ("def %s(%s):\n"%(function, args) +
        #          data.getVar(function, expand=0) + "\n")
        #(g, l) = execlite(source, data, funcimports, "%s"%(function))
        #retval = eval("%s()"%(function))
        #print "funcimports = %s"%(funcimports.keys())

        #retval = evallite("%s()\n"%(function), data, funcimports)

        retval = hook(data)

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
