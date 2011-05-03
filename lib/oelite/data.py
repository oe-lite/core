import sys
import string
import os
import re
import codeop
import warnings
from pysqlite2 import dbapi2 as sqlite
from oelite.pyexec import inlineeval
from oebakery import die, err, warn, info, debug
from collections import MutableMapping


NO_EXPANSION      = 0
FULL_EXPANSION    = 1
PARTIAL_EXPANSION = 2
CLEAN_EXPANSION   = 3


class ExpansionStack:

    def __init__(self):
        self.stack = []
        self.python = False
        return

    def push(self, var):
        if var in self.stack:
            raise Exception("Circular expansion: %s"%("->".join(self.stack)))
        self.stack.append(var)
        return

    def pop(self):
        del self.stack[-1:]
        return


pythonfunc_code_cache = {}
    

class Data(MutableMapping):


    def __init__(self, dbfile=":memory:", data=None):
        super(Data, self).__init__()
        self.db = sqlite.connect(dbfile)
        if not self.db:
            raise Exception("could not create in-memory sqlite db")
        self.db.text_factory = str
        self.dbc = self.db.cursor()
        self.dbfile = dbfile
        if isinstance(data, str):
            self.dbc.executescript(data)
        elif isinstance(data, dict):
            self.create_tables()
            self.import_dict(data)
        else:
            self.create_tables()
        self.pythonfunc_init()
        self.expand_stack = ExpansionStack()
        return


    def import_dict(self, data):
        for var in data:
            if var == "__file_mtime":
                for (filename, mtime) in data[var][""]:
                    self.setFileMtime(filename, mtime)
                continue
            for (flag, value) in data[var].items():
                #print "importing %s[%s]=%s"%(var,flag,value)
                self.setVarFlag(var, flag, value)
        return
            

    def full_dump(self):
        return os.linesep.join([line for line in self.db.iterdump()])


    def copy(self, dbfile=":memory:"):
        dump = self.full_dump()
        return Data(dbfile=dbfile, data=dump)


    def __repr__(self):
        return 'Data(%s)'%(repr(self.dbfile))


    def __str__(self):
        return self.full_dump()


    def __eq__(self):
        raise Exception("Data.__eq__() not implemented")
        return False


    def __hash__(self):
        raise Exception("Data.__hash__() not implemented")
        return


    def __nonzero__(self):
        raise Exception("Data.__nonzero__() not implemented")
        return True


    def __len__(self): # required by Sized
        raise Exception("Data.__len__() not implemented")


    def __getitem__(self, key): # required by Mapping
        return self.get(key, 0)


    def __setitem__(self, key, value): # required by MutableMapping
        self.set(key, value)
        return value


    def __delitem__(self, key): # required by MutableMapping
        #print "del %s"%(key)
        var_id = self.var_id(key)
        self.dbc.execute(
            "DELETE FROM var_val WHERE var_val.var=:var_id", locals())
        return


    def __iter__(self): # required by Iterable
        return self.getVarNames().__iter__()


    def __reversed__(self):
        raise Exception("Data.__reversed__() not implemented")


    def __contains__(self, item): # required by Container
        val = self.get(item, 0)
        return val is not None


    def keys(self):
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT var.name FROM var, var_val WHERE var.id=var_val.var",
            locals()))


    def create_tables(self):
        c = self.db.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS var ( "
                  "id INTEGER PRIMARY KEY, "
                  "name TEXT UNIQUE ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS var_val ( "
                  "var INTEGER UNIQUE ON CONFLICT REPLACE, "
                  "val TEXT )")

        c.execute("CREATE TABLE IF NOT EXISTS var_flag ( "
                  "var INTEGER, "
                  "flag TEXT, "
                  "val TEXT, "
                  "UNIQUE (var, flag) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS var_override ( "
                  "var INTEGER, "
                  "override TEXT, "
                  "val TEXT, "
                  "UNIQUE (var, override) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS var_append ( "
                  "var INTEGER, "
                  "append TEXT, "
                  "val TEXT, "
                  "UNIQUE (var, append) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS expand_cache ( "
                  "var INTEGER UNIQUE ON CONFLICT REPLACE, "
                  "val TEXT )")

        c.execute("CREATE TABLE IF NOT EXISTS expand_cache_deps ( "
                  "var INTEGER, "
                  "dep INTEGER, "
                  "UNIQUE (var, dep) ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS hook ( "
                  "name     TEXT, "
                  "function TEXT, "
                  "sequence INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS hook_dependency ( "
                  "name     TEXT, "
                  "function TEXT, "
                  "after    TEXT )")

        c.execute("CREATE TABLE IF NOT EXISTS file ( "
                  "fn TEXT PRIMARY KEY ON CONFLICT REPLACE, "
                  "mtime TEXT  )")

        return


    def var_id(self, var):
        self.dbc.execute(
            "INSERT INTO var (name) VALUES (:var)", locals())
        return flatten_single_value(self.dbc.execute(
                "SELECT id FROM var WHERE name=:var", locals()))



    def set(self, var, val):
        #print "set %s=%s"%(var, val)
        var_id = self.var_id(var)
        self.dbc.execute(
            "INSERT INTO var_val (var, val) VALUES (:var_id, :val)", locals())
        self.dbc.execute(
            "DELETE FROM"
            "  expand_cache "
            "WHERE"
            "  EXISTS ("
            "    SELECT * FROM expand_cache_deps AS deps"
            "    WHERE deps.dep=:var_id"
            "    AND expand_cache.var=deps.var"
            "  ) OR expand_cache.var=:var_id", locals())
        self.dbc.execute(
            "DELETE FROM"
            "  expand_cache_deps "
            "WHERE"
            "  EXISTS ("
            "    SELECT * FROM expand_cache_deps AS deps"
            "    WHERE deps.dep=:var_id"
            "    AND expand_cache_deps.var=deps.var"
            "  ) OR expand_cache_deps.var=:var_id", locals())
        #import sys
        #print self.full_dump()
        #sys.exit(42)
        return


    def set_flag(self, var, flag, val):
        #print "set_flag %s[%s]=%s"%(var, flag, val)
        var_id = self.var_id(var)
        self.dbc.execute(
            "INSERT INTO var_flag (var, flag, val) "
            "VALUES (:var_id, :flag, :val)", locals())
        return


    def get(self, var, expand=True):
        return self._get(var, expand)[0]


    def _get(self, var, expand=True):
        #print "_get %s"%(var)
        var_id = self.var_id(var)
        if expand:
            val = flatten_single_value(self.dbc.execute(
                    "SELECT val FROM expand_cache WHERE var=:var_id", locals()))
            if val is not None:
                #print "get returning cached %s=%s"%(var, repr(val))
                return (val, None)
        val = flatten_single_value(self.dbc.execute(
            "SELECT val FROM var_val WHERE var=:var_id", locals()))
        if not expand:
            #print "get returning unexpanded %s=%s"%(var, repr(val))
            return (val, None)
        if not val:
            #print "get returning %s=%s"%(var, repr(val))
            return (val, None)
        #print "get expanding %s=%s"%(var, repr(val))
        expand_method = self.get_flag(var, "expand") or FULL_EXPANSION
        if expand_method == NO_EXPANSION:
            #print "get not expanding anyway"
            return (val, None)
        self.expand_stack.push(var)
        (val, deps) = self._expand(val, expand_method)
        self.expand_stack.pop()
        self.dbc.execute(
            "INSERT INTO expand_cache (var, val) "
            "VALUES (:var_id, :val)", locals())
        for dep in deps:
            # FIXME: replace this for loop with proper pysqlite construct
            self.dbc.execute(
                "INSERT INTO expand_cache_deps (var, dep) "
                "VALUES (:var_id, :dep)", locals())
        #print "get returning %s=%s"%(var, repr(val))
        return (val, deps)


    def get_flag(self, var, flag, expand=False):
        var_id = self.var_id(var)
        val = flatten_single_value(self.dbc.execute(
                "SELECT var_flag.val FROM var_flag, var "
                "WHERE var.name=:var AND var_flag.flag=:flag "
                "AND var_flag.var=var.id", locals()))
        if val and expand:
            (val, deps) = self.expand(val, EXPAND_FULL)
        return val


    def get_list(self, var, expand=True):
        return (self.get(var, expand) or "").split()


    def get_flag_list(self, var, flag, expand=0):
        return (self.get_flag(var, flag, expand) or "").split()


    def get_vars(self, flag=None):
        if flag:
            return flatten_single_column_rows(self.dbc.execute(
                    "SELECT var.name FROM var, var_flag "
                    "WHERE var_flag.flag=:flag AND var_flag.var=var.id",
                    locals()))
        return flatten_single_column_rows(self.dbc.execute(
                "SELECT name FROM var"))


    def get_flags(self, var):
        flags = {}
        for (flag, val) in self.dbc.execute(
            "SELECT var_flag.flag,var_flag.val "
            "FROM var,var_flag "
            "WHERE var.name=:var AND var_flag.var=var.id",
            locals()):
            flags[flag] = val
        return flags


    def pythonfunc_init(self):
        self.pythonfunc_cache = {}
        imports = (self.get("OE_IMPORTS", expand=0) or "")
        g = {}
        g["__builtins__"] = globals()["__builtins__"]
        for module_name in imports.split():
            #print "importing module", module_name
            base_name = module_name.split(".")[0]
            g[base_name] = __import__(module_name, g, [], [], 0)
        self.pythonfunc_globals = g
        return


    def get_pythonfunc_globals(self):
        g = self.pythonfunc_globals.copy()
        #g.update({"d": self})
        return g


    def get_autoimport_pythonfuncs(self, g=None):
        return self.get_pythonfuncs(self.get_vars(flag="autoimport"), g)


    def get_pythonfuncs(self, functions, g=None):
        if g is None:
            g = self.get_pythonfunc_globals()
        pythonfuncs = {}
        for function in functions:
            pythonfuncs[function] = self.get_pythonfunc(function, g)
        return pythonfuncs


    def get_pythonfunc(self, function, g=None, recursion_path=[]):
        #if function in self.pythonfunc_cache:
        #    return self.pythonfunc_cache[function]
        recursion_path.append(function)
        if g is None:
            g = self.get_pythonfunc_globals()
        #l = {"d": self}
        funcimports = {}
        for func in (self.get_flag(function, "funcimport", FULL_EXPANSION)
                     or "").split():
            if func in funcimports:
                continue
            if func in recursion_path:
                raise Exception("circular funcimport")
            funcimports[func] = self.get_pythonfunc(func, g, recursion_path)
        code = self.get_pythonfunc_code(function)
        #print "get_pythonfunc %s l=%s"%(function, l)
        g.update(funcimports)
        l = {}
        eval(code, g, l)
        self.pythonfunc_cache[function] = l[function]
        return l[function]


    def get_pythonfunc_code(self, var):
        if not self.get_flag(var, "python"):
            raise Exception("%s is not a python function"%(var))
        args = self.get_flag(var, "args") or ""
        body = self.get(var, expand=0)
        if not body or body.strip() == "":
            body = "    pass"
        source = "def %s(%s):\n%s\n"%(var, args, body)
        if source in pythonfunc_code_cache:
            return pythonfunc_code_cache[source]
        try:
            code = codeop.compile_command(source, "<%s>"%(var))
        except SyntaxError, e:
            print "Syntax error in python function: %s"%(var)
            print e
            #print source
            raise
        if not code:
            raise Exception("%s is not valid Python code"%(var))
        pythonfunc_code_cache[source] = code
        return code


    def add_hook(self, name, function, sequence=1, after=[], before=[]):
        #print "addhook %s %s after=%s before=%s"%(name, function, after,before)
        self.dbc.execute(
            "INSERT INTO hook (name, function, sequence) "
            "VALUES (:name, :function, :sequence)", locals())
        def word_generator(l):
            for w in l:
                yield (w,)
        if after:
            self.dbc.executemany(
                "INSERT INTO hook_dependency (name, function, after) " +
                "VALUES ('%s', '%s', ?)"%(name, function),
                word_generator(after))
        if before:
            self.dbc.executemany(
                "INSERT INTO hook_dependency (name, function, after) " +
                "VALUES ('%s', ?, '%s')"%(name, function),
                word_generator(list(before)))
        return


    def get_hooks(self, name):
        hooks = flatten_single_column_rows(self.dbc.execute(
                "SELECT function FROM hook WHERE name=:name "
                "ORDER BY sequence, rowid", locals()))
        #print "hooks = %s"%(hooks)
        num_hooks = len(hooks)
        moved = []
        i = 0
        while i < num_hooks:
            #print "get_hooks i=%s hooks=%s"%(i, hooks)
            function = hooks[i]
            after = flatten_single_column_rows(self.dbc.execute(
                    "SELECT after FROM hook_dependency "
                    "WHERE name=:name AND function=:function", locals()))
            #print "get_hooks function=%s after=%s"%(function, after)
            if not after:
                i += 1
                continue
            move_after = None
            for j in xrange(i+1, num_hooks):
                if hooks[j] in after:
                    move_after = max(move_after, j)
            if not move_after:
                i += 1
                continue
            if function in moved:
                raise Exception("circular hook dependency detected")
            del hooks[i]
            hooks.insert(move_after, function)
            moved.append(function)
        return hooks


    def setFileMtime(self, fn, mtime):
        self.dbc.execute(
            "INSERT INTO file (fn, mtime) VALUES (:fn, :mtime)",
            locals())
        return


    def getFileMtime(self, fn):
        return flatten_single_value(self.dbc.execute(
            "SELECT mtime FROM file WHERE fn=:fn",
            locals()))


    def dict(self):
        varflags = self.dbc.execute(
            "SELECT var,flag,val FROM varflag",
            locals())
        d = {}
        for (var, flag, val) in varflags:
            if not var in d:
                d[var] = {}
            d[var][flag] = val
        return d


    def expand(self, string, method=FULL_EXPANSION):
        """Expand string using variable data.
    
        Arguments:
        string -- String to expand
        method -- Expansion method (default: FULL_EXPANSION)
    
        Expansion methods:
        EXPAND_NONE -- no recursive expansion
        EXPAND_FULL -- full expansion, all variables must be expanded
        EXPAND_PARTIAL -- partial, allow unknown variables to remain unexpanded
        EXPAND_CLEAN -- clean, expand unknown variables to empty string
        """
        #print "expand method=%s string=%s"%(method, repr(string))
        (new_string, deps) = self._expand(string, method)
        return new_string


    #def _expand(self, string, method):
    #    #print "_expand method=%s string=%s"%(method, repr(string))
    #    orig_string = string
    #    var_re    = re.compile(r"\${[^{}]+}")
    #    python_re = re.compile(r"\${@.+?}")
    #    python_match = python_re.search(string)
    #    deps = set()
    #    if python_match:
    #        python_source = python_match.group(0)[3:-1]
    #        self.expand_stack.push("python %s"%(repr(python_source)))
    #        python_output = inlineeval(python_source, self)
    #        #print "python_output=%s"%(repr(python_output))
    #        (expanded_output, python_deps) = self._expand(python_output, method)
    #        string = (string[:python_match.start(0)] +
    #                  expanded_output +
    #                  string[python_match.end(0):])
    #        #print "after python string: %s"%(repr(string))
    #        deps.add("python")
    #        deps.union(python_deps)
    #        self.expand_stack.pop()
    #    new_string = ""
    #    string_ptr = 0
    #    for var_match in var_re.finditer(string):
    #        var = var_match.group(0)[2:-1]
    #        (val, recdeps) = self._get(var)
    #        new_string += string[string_ptr:var_match.start(0)] + "%s"%(val,)
    #        string_ptr = var_match.end(0)
    #        deps.add(var)
    #        deps.union(recdeps)
    #    new_string += string[string_ptr:]
    #    #print "returning expanded string %s"%(repr(new_string))
    #    return (new_string, deps)


    def _expand(self, string, method):
        #print "_expand method=%s string=%s"%(method, repr(string))
        orig_string = string
        var_re    = re.compile(r"\${[^@{}]+}")
        python_re = re.compile(r"\${@.+?}")
        deps = set()
        expanded_string = ""
        string_ptr = 0
        for var_match in var_re.finditer(string):
            var = var_match.group(0)[2:-1]
            (val, recdeps) = self._get(var)
            expanded_string += (string[string_ptr:var_match.start(0)] +
                                "%s"%(val,))
            string_ptr = var_match.end(0)
            deps.add(var)
            if recdeps:
                deps.union(recdeps)
        expanded_string += string[string_ptr:]
        python_match = python_re.search(expanded_string)
        if python_match:
            python_source = python_match.group(0)[3:-1]
            self.expand_stack.push("python %s"%(repr(python_source)))
            python_output = inlineeval(python_source, self)
            #print "python_output=%s"%(repr(python_output))
            (expanded_output, recdeps) = self._expand(python_output, method)
            expanded_string = (expanded_string[:python_match.start(0)] +
                               expanded_output +
                               expanded_string[python_match.end(0):])
            #print "after python string: %s"%(repr(expanded_string))
            deps.add("python")
            if recdeps:
                deps.union(recdeps)
            self.expand_stack.pop()
        #print "returning expanded string %s"%(repr(expanded_string))
        return (expanded_string, deps)


    def appendVar(self, var, value, separator=""):
        current = self.get(var, NO_EXPANSION)
        if current == None:
            self.set(var, value)
        else:
            self.set(var, current + separator + value)

    def appendVarFlag(self, var, flag, value, separator=""):
        current = self.get_flag(var, flag)
        if current == None:
            self.set_flag(var, flag, value)
        else:
            self.set_flag(var, flag, current + separator + value)

    def prependVar(self, var, value, separator=""):
        current = self.get(var, NO_EXPANSION)
        if current == None:
            self.set(var, value)
        else:
            self.set(var, value + separator + current)

    def prependVarFlag(self, var, flag, value, separator=""):
        current = self.get_flag(var, flag)
        if current == None:
            self.set_flag(var, flag, value)
        else:
            self.set_flag(var, flag, value + separator + current)


    def setVar(self, var, val):
        warnings.warn("setVar() is deprecated, use set()")
        return self.set(var, val)


    def setVarFlag(self, var, flag, val):
        warnings.warn("setVarFlag() is deprecated, use set_flag()")
        return self.set_flag(var, flag, val)


    def getVar(self, var, expand=1):
        warnings.warn("getVar() is deprecated, use get()")
        return self.get(var, expand)


    def getVarFlag(self, var, flag, expand=0):
        warnings.warn("getVarFlag() is deprecated, use get_flag()")
        return self.get_flag(var, flag, expand)


    def delVar(self, var):
        warnings.warn("delVar() is deprecated, use del built-in")
        del self[var]
        return


    def createCopy(self):
        warnings.warn("createCopy() is deprecated, use copy()")
        return self.copy()


def flatten_single_value(rows):
    row = rows.fetchone()
    if row is None:
        return None
    return row[0]


def flatten_one_string_row(rows):
    row = rows.fetchone()
    if row is None:
        return None
    return str(row[0])


def flatten_single_column_rows(rows):
    rows = rows.fetchall()
    if not rows:
        return []
    for i in range(len(rows)):
        rows[i] = rows[i][0]
    return rows


def var_to_tuple(v):
    return (v,)

def tuple_to_var(t):
    return t[0]



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
    "BBRECIPES",
    "BBRECIPES_PRETTY",
    "FILE",
    "_task_deps",
]

builtin_nohash_prefix = [
    "OE_REMOTE_",
    "OE_MODULE_",
]


def dump_var(key, o=sys.__stdout__, d=Data(), pretty=True, dynvars = {}):
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


def dump(o=sys.__stdout__, d=Data(),
         pretty=True, nohash=False):

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
