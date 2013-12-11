from oelite.meta import *
from oelite.dbutil import *
import oelite.util

import sys
import os
import copy
from pysqlite2 import dbapi2 as sqlite
from collections import Mapping


class SqliteMetaCache(Mapping):

    def __init__(self, dbfile=":memory:", recipes=None):
        #dbfile=":memory:"
        self.dbfile = dbfile
        init = True
        if dbfile != ":memory:":
            oelite.util.makedirs(os.path.dirname(dbfile))
            if os.path.exists(dbfile):
                if recipes:
                    print "deleting file %s"%(dbfile)
                    os.unlink(dbfile)
                else:
                    init = False
        print "dbfile =", dbfile
        self.db = sqlite.connect(dbfile, isolation_level=None)
        print "connected"
        if not self.db:
            raise Exception("could not create sqlite db")
        self.db.text_factory = str
        self.dbc = self.db.cursor()
        if init:
            self.init_db()
        print "created tables"
        self.dbc.execute("BEGIN EXCLUSIVE TRANSACTION")
        self.meta = {}
        if recipes:
            self.add_recipe_meta(recipes)
        for (type,) in self.dbc.execute(
            "SELECT DISTINCT type FROM var_flag"):
            print "creating type=%s"%(type)
            self.meta[type] = SqliteMeta(self, type)
        print "commit"
        self.dbc.execute("COMMIT TRANSACTION")
        self.db.commit()
        print "done"
        return


    def __repr__(self):
        return '%s()'%(self.__class__.__name__)

    def __eq__(self):
        raise Exception("__eq__() not implemented")

    def __hash__(self):
        raise Exception("__hash__() not implemented")

    def __nonzero__(self):
        raise Exception("__nonzero__() not implemented")

    def __len__(self): # required by Sized
        raise Exception("__len__() not implemented")

    def __getitem__(self, key): # required by Mapping
        return self.meta[key]


    def __iter__(self):
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT DISTINCT type FROM var_flag")).__iter__()


    def init_db(self):
        c = self.db.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS var_flag ( "
                  "type     TEXT, "
                  "var      TEXT, "
                  "flag     TEXT, "
                  "val      TEXT, "
                  "UNIQUE (type, var, flag) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS var_override ( "
                  "type     TEXT, "
                  "var      TEXT, "
                  "override TEXT, "
                  "val      TEXT, "
                  "UNIQUE (type, var, override) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS var_append ( "
                  "type     TEXT, "
                  "var      TEXT, "
                  "append   TEXT, "
                  "val      TEXT, "
                  "UNIQUE (type, var, append) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS expand_cache ( "
                  "type     TEXT, "
                  "var      TEXT UNIQUE ON CONFLICT REPLACE, "
                  "val      TEXT )")

        c.execute("CREATE TABLE IF NOT EXISTS expand_cache_deps ( "
                  "type     TEXT, "
                  "var      TEXT, "
                  "dep      TEXT, "
                  "UNIQUE (type, var, dep) ON CONFLICT IGNORE )")

        c.execute("CREATE TABLE IF NOT EXISTS hook ( "
                  "name     TEXT, "
                  "function TEXT, "
                  "sequence INTEGER )")

        c.execute("CREATE TABLE IF NOT EXISTS hook_dependency ( "
                  "name     TEXT, "
                  "function TEXT, "
                  "after    TEXT )")

        c.execute("CREATE TABLE IF NOT EXISTS input_mtime ( "
                  "fn       TEXT, "
                  "oepath   TEXT, "
                  "mtime    TEXT, "
                  "UNIQUE (fn, oepath, mtime) ON CONFLICT IGNORE )")

        return


    def add_recipe_meta(self, recipe_meta):
        # recipe_meta is a dict of recipe_type -> oelite.meta.DictMeta
        for recipe_type in recipe_meta:
            meta = recipe_meta[recipe_type].meta
            print "adding variables"
            #self.dbc.executemany(
            #    "INSERT INTO var_flag (var, flag, val, type) "
            #    "VALUES (?, ?, ?, ?)",
            #    meta.get_var_flags(append=(recipe_type,)))
            #self.dbc.executemany(
            #    "INSERT INTO input_mtime (fn, oepath, mtime) VALUES (?, ?, ?)",
            #    meta.get_input_mtimes())
            print "done"
        return


    def is_current(self):
        return False
#        for recipe_type in recipe_meta:
    #        meta = recipe_meta[recipe_type]
    #        for (searchpath, cache_mtime) in meta.get_input_mtime():
    #            if isinstance(searchpath, str):
    #                cur_mtime = os.path.getmtime(searchpath)
    #            if



class SqliteMeta(MetaData):


    def __init__(self, cache, type):
        self.cache = cache
        self.type = type
        self.dbc = cache.db.cursor()
        super(SqliteMeta, self).__init__()
        return


    def __str__(self):
        return oelite.dbutil.dump(self.cache.db)


    def __len__(self): # required by Sized
        raise Exception("__len__ not implemented yet")


    def keys(self):
        return flatten_single_column_rows(self.dbc.execute(
            "SELECT var FROM var_flag WHERE flag=''"))


    def set(self, var, val):
        #print "set %s=%s"%(var, val)
        raise Exception(42)
        type = self.type
        self.dbc.execute(
            "INSERT INTO var_val (type, var, flag, val) VALUES (?, ?, ?, ?)",
            self.type, var, "", val)
        self.dbc.execute(
            "DELETE FROM"
            "  expand_cache "
            "WHERE"
            "  EXISTS ("
            "    SELECT * FROM expand_cache_deps AS deps"
            "    WHERE deps.type=:type AND deps.dep=:var"
            "    AND expand_cache.var=deps.var"
            "    AND expand_cache.type=:type"
            "  ) OR expand_cache.var=:var", locals())
        self.dbc.execute(
            "DELETE FROM"
            "  expand_cache_deps "
            "WHERE"
            "  EXISTS ("
            "    SELECT * FROM expand_cache_deps AS deps"
            "    WHERE deps.type=:type AND deps.dep=:var"
            "    AND expand_cache_deps.var=deps.var"
            "    AND expand_cache.type=:type"
            "  ) OR expand_cache_deps.var=:var", locals())
        return


    def set_flag(self, var, flag, val):
        #print "set_flag %s[%s]=%s"%(var, flag, val)
        raise Exception(42)
        type = self.type
        self.dbc.execute(
            "INSERT INTO var_flag (type, var, flag, val) "
            "VALUES (:type, :var, :flag, :val)", locals())
        return


    def get(self, var, expand=True):
        return self._get(var, expand)[0]


    def _get(self, var, expand=True):
        #print "_get %s"%(var)
        type = self.type
        if expand:
            val = flatten_single_value(self.dbc.execute(
                    "SELECT val FROM expand_cache "
                    "WHERE type=:type AND var=:var", locals()))
            if val is not None:
                #print "get returning cached %s=%s"%(var, repr(val))
                return (val, None)
        val = flatten_single_value(self.dbc.execute(
            "SELECT val FROM var_flag "
            "WHERE type=:type AND var=:var AND flag=''", locals()))
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
            "INSERT INTO expand_cache (type, var, val) "
            "VALUES (:type, :var, :val)", locals())
        for dep in deps:
            # FIXME: replace this for loop with proper pysqlite construct
            self.dbc.execute(
                "INSERT INTO expand_cache_deps (type, var, dep) "
                "VALUES (:type, :var, :dep)", locals())
        #print "get returning %s=%s"%(var, repr(val))
        return (val, deps)


    def get_flag(self, var, flag, expand=False):
        type = self.type
        val = flatten_single_value(self.dbc.execute(
                "SELECT val FROM var_flag "
                "WHERE type=:type AND var=:var AND flag=:flag",
                locals()))
        if val and expand:
            (val, deps) = self.expand(val, EXPAND_FULL)
        return val


    def del_var(self, var):
        #print "del_var %s"%(var)
        raise Exception(42)
        self.dbc.execute(
            "DELETE FROM var WHERE name=? AND type=?", var, self.type)
        return


    def get_list(self, var, expand=True):
        return (self.get(var, expand) or "").split()


    def get_flag_list(self, var, flag, expand=0):
        return (self.get_flag(var, flag, expand) or "").split()


    def get_vars(self, flag=""):
        #print "get_vars flag=%s"%(flag)
        type = self.type
        if flag:
            return flatten_single_column_rows(self.dbc.execute(
                    "SELECT DISTINCT var FROM var_flag "
                    "WHERE type=:type AND flag=:flag",
                    locals()))
        #print "get_vars: %s"%(vars)
        return vars


    def get_flags(self, var):
        type = self.type
        flags = {}
        for (flag, val) in self.dbc.execute(
            "SELECT flag, val FROM var,var_flag "
            "WHERE type=:type AND var=:var",
            locals()):
            flags[flag] = val
        return flags


    def add_hook(self, name, function, sequence=1, after=[], before=[]):
        return


    def get_hooks(self, name):
        return []
