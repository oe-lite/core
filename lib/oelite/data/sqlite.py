import os, codeop
from pysqlite2 import dbapi2 as sqlite
from base import BaseData
import oelite.pyexec as pyexec


class SqliteData(BaseData):

    def __init__(self, dbfile=":memory:", data=None):
        super(SqliteData, self).__init__()
        self.db = sqlite.connect(dbfile)
        self.db.text_factory = str
        if not self.db:
            raise Exception("could not create in-memory sqlite db")
        self.dbfile = dbfile
        if isinstance(data, str):
            self.db.executescript(data)
        elif isinstance(data, dict):
            self.create_tables()
            self.import_dict(data)
        else:
            self.create_tables()
        self.pythonfunc_init()
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
            

    def createCopy(self, dbfile=":memory:"):
        dump = self.full_dump()
        return SqliteData(dbfile=dbfile, data=dump)


    def pythonfunc_init(self):
        self.pythonfunc_cache = {}
        imports = (self.getVar("OE_IMPORTS", expand=0) or "")
        #print "pythonfunc_init OE_IMPORTS=%s FILE=%s"%(imports, self.getVar('FILE'))
        g = {}
        g["__builtins__"] = globals()["__builtins__"]
        for module_name in imports.split():
            #print "importing module", module_name
            base_name = module_name.split(".")[0]
            g[base_name] = __import__(module_name, g, [], [], 0)
        self.pythonfunc_globals = g
        return


    def __repr__(self):
        return 'SqliteData(%s)'%(repr(self.dbfile))


    def __str__(self):
        return self.full_dump()


    def __eq__(self):
        raise Exception("SqliteData.__eq__() not implemented")
        return False


    def __hash__(self):
        raise Exception("SqliteData.__hash__() not implemented")
        return


    def __nonzero__(self):
        raise Exception("SqliteData.__nonzero__() not implemented")
        return True


    def __len__(self): # required by Sized
        raise Exception("SqliteData.__len__() not implemented")


    def __getitem__(self, key): # required by Mapping
        return self.getVar(key, 0)


    def __setitem__(self, key, value): # required by MutableMapping
        self.setVar(key, value)
        return value


    def __delitem__(self, key): # required by MutableMapping
        raise Exception("SqliteData.__del__() not implemented")


    def __iter__(self): # required by Iterable
        return self.getVarNames().__iter__()


    def __reversed__(self):
        raise Exception("SqliteData.__reversed__() not implemented")


    def __contains__(self, item): # required by Container
        val = self.getVar(item, 0)
        return val is not None


    def keys(self):
        return flatten_single_column_rows(self.db.execute(
            "SELECT var FROM varflag WHERE flag=''",
            locals()))


    def create_tables(self):
        c = self.db.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS var ( "
                  "name TEXT PRIMARY KEY ON CONFLICT REPLACE, "
                  "val TEXT )")

        c.execute("CREATE TABLE IF NOT EXISTS varflag ( "
                  "var TEXT, "
                  "flag TEXT, "
                  "val TEXT, "
                  "UNIQUE (var, flag) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS file ( "
                  "fn TEXT PRIMARY KEY ON CONFLICT REPLACE, "
                  "mtime TEXT  )")

        c.execute("CREATE TABLE IF NOT EXISTS anonfunc ( "
                  "seqno INTEGER PRIMARY KEY, "
                  "fn TEXT, "
                  "line INTEGER, "
                  "source TEXT )")

        c.execute("CREATE TABLE IF NOT EXISTS hook ( "
                  "name     TEXT, "
                  "function TEXT, "
                  "sequence INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS hook_dependency ( "
                  "name     TEXT, "
                  "function TEXT, "
                  "after    TEXT )")

        return


    def addAnonymousFunction(self, fn, line, source):
        self.db.execute(
            "INSERT INTO anonfunc (seqno, fn, line, source) "
            "VALUES (NULL, :fn, :line, :source)", locals())
        return


    def get_anonfuncs(self):
        return self.db.execute(
            "SELECT fn, line, source FROM anonfunc ORDER BY seqno").fetchall()


    def add_hook(self, name, function, sequence=1, after=[], before=[]):
        #print "addhook %s %s after=%s before=%s"%(name, function, after,before)
        self.db.execute(
            "INSERT INTO hook (name, function, sequence) "
            "VALUES (:name, :function, :sequence)", locals())
        def word_generator(l):
            for w in l:
                yield (w,)
        if after:
            self.db.executemany(
                "INSERT INTO hook_dependency (name, function, after) " +
                "VALUES ('%s', '%s', ?)"%(name, function),
                word_generator(after))
        if before:
            self.db.executemany(
                "INSERT INTO hook_dependency (name, function, after) " +
                "VALUES ('%s', ?, '%s')"%(name, function),
                word_generator(list(before)))
        return


    #def add_hook_dependency(self, name, function, after):
    #    self.db.execute(
    #        "INSERT INTO hook_dependency (name, function, after) "
    #        "VALUES (:name, :function, :after)", locals())
    #    return


    def get_hooks(self, name):
        hooks = flatten_single_column_rows(self.db.execute(
                "SELECT function FROM hook WHERE name=:name "
                "ORDER BY sequence, rowid", locals()))
        #print "hooks = %s"%(hooks)
        num_hooks = len(hooks)
        moved = []
        i = 0
        while i < num_hooks:
            #print "get_hooks i=%s hooks=%s"%(i, hooks)
            function = hooks[i]
            after = flatten_single_column_rows(self.db.execute(
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

    def full_dump(self):
        return os.linesep.join([line for line in self.db.iterdump()])


    def setVar(self, var, val):
        #print "setVar %s=%s"%(var, val)
        self.db.execute(
            "INSERT INTO var (name, val) VALUES (:var, :val)", locals())
        return


    def setVarFlag(self, var, flag, val):
        self.db.execute(
            "INSERT INTO varflag (var, flag, val) VALUES (:var, :flag, :val)",
            locals())
        return


    # expand=1|True for strict expansion, expand=2 for allow_unexpand
    def getVar(self, var, expand=1):
        #print "getVar %s"%(var)
        val = flatten_single_value(self.db.execute(
            "SELECT val FROM var WHERE name=:var",
            locals()))
        if val and expand:
            #print "getVar expanding %s = %s"%(var, repr(val))
            val = self.expand(val, (expand == 2))
        #print "getVar %s=%s"%(var, val)
        return val


    def getVarFlag(self, var, flag, expand=0):
        val = flatten_single_value(self.db.execute(
                "SELECT val FROM varflag WHERE var=:var AND flag=:flag",
                locals()))
        if val and expand:
            val = self.expand(val, (expand == 2))
        return val


    def getVarSplit(self, var, expand=1):
        return (self.getVar(var, expand) or "").split()


    def getVarFlagSplit(self, var, flag, expand=0):
        return (self.getVarFlag(var, flag, expand) or "").split()


    def getVarsWithFlag(self, flag):
        return flatten_single_column_rows(self.db.execute(
            "SELECT var FROM varflag WHERE flag=:flag", locals()))


    def getVarNames(self):
        return flatten_single_column_rows(self.db.execute(
                "SELECT name FROM var"))


    def get_pythonfunc_globals(self):
        g = self.pythonfunc_globals.copy()
        #g.update({"d": self})
        return g


    def get_autoimport_pythonfuncs(self, g=None):
        return self.get_pythonfuncs(self.getVarsWithFlag("autoimport"), g)


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
        for func in (self.getVarFlag(function, "funcimport", 1) or "").split():
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
        # FIXME: implement code/compile cache here
        is_python = self.getVarFlag(var, "python", 0)
        if not is_python:
            raise Exception("%s is not a python function"%(var))
        args = self.getVarFlag(var, "args") or ""
        body = self.getVar(var, expand=0)
        if not body or body.strip() == "":
            body = "    pass"
        source = "def %s(%s):\n%s\n"%(var, args, body)
        try:
            code = codeop.compile_command(source, "<%s>"%(var))
        except SyntaxError, e:
            print "Syntax error in python function: %s"%(var)
            print e
            #print source
            raise
        if not code:
            raise Exception("%s is not valid Python code"%(var))
        return code


    def setFileMtime(self, fn, mtime):
        self.db.execute(
            "INSERT INTO file (fn, mtime) VALUES (:fn, :mtime)",
            locals())
        return


    def getFileMtime(self, fn):
        return flatten_single_value(self.db.execute(
            "SELECT mtime FROM file WHERE fn=:fn",
            locals()))


    def dict(self):
        varflags = self.db.execute(
            "SELECT var,flag,val FROM varflag",
            locals())
        d = {}
        for (var, flag, val) in varflags:
            if not var in d:
                d[var] = {}
            d[var][flag] = val
        return d


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
