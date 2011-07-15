from oebakery import die, err, warn, info, debug
from oelite import InvalidRecipe
import oelite.meta
from oelite.dbutil import *

import sys
import os
import cPickle
import warnings


def unpickle(file, filename, cookbook):
    type = cPickle.load(file)
    meta = oelite.meta.dict.unpickle(file)
    return OEliteRecipe(filename, type, meta, cookbook)


class OEliteRecipe:

    def pickle(self, file):
        cPickle.dump(self.type, file, 2)
        self.meta.pickle(file)


    def __init__(self, filename, type, meta, cookbook):
        self.filename = filename
        self.type = type
        self.cookbook = cookbook
        self.meta = meta
        self.name = self.meta.get("PN")
        self.version = self.meta.get("PV")
        self.priority = int(self.meta.get("DEFAULT_PREFERENCE") or "0")
        self._datahash = None
        self._srchash = "FOOBAR"
        self._hash = None
        return


    def __str__(self):
        return "%s:%s_%s"%(self.type, self.name, self.version)

    def set_id(self, id):
        self.id = id
        return

    def get(self, var):
        return self.meta.get(var)

    def get_flag(self, var, flag):
        return self.meta.get_flag(var, flag)

    def get_task_names(self):
        return self.meta.get_vars(flag="task")

    def get_depends(self):
        depends = []
        for type, item, version in self.cookbook.dbc.execute(
            "SELECT type, item, version FROM recipe_depend "
            "WHERE recipe_depend.recipe=?", (self.id,)):
            if version is None:
                depends.append("%s:%s"%(type, item))
            else:
                depends.append("%s:%s_%s"%(type, item, version))
        return depends
        #return self.meta.get_list("DEPENDS")

    def get_rdepends(self):
        depends = []
        for type, item in self.cookbook.dbc.execute(
            "SELECT type, item FROM recipe_rdepend WHERE recipe=?", (self.id,)):
            depends.append("%s:%s"%(type, item))
        return depends
        #return self.meta.get_list("RDEPENDS")


    def post_parse(self):
        #print "recipe post parse %s"%(self.filename)

        # FIXME: refactor to post_recipe_parse hook
        name = self.meta.get("PN")
        if not name:
            raise InvalidRecipe("no PN in %s:%s"%(
                    filename, type))

        # FIXME: refactor to post_recipe_parse hook
        version = self.meta.get("PV") or "0"
        if "PR" in self.meta:
            version += "-" + self.meta.get("PR")

        # FIXME: refactor to post_recipe_parse hook
        preference = self.meta.getVar("DEFAULT_PREFERENCE", 1) or "0"
        try:
            preference = int(preference)
        except ValueError, e:
            raise InvalidRecipe("invalid DEFAULT_PREFERENCE=%s in %s:%s"%(
                    preference, filename, recipe_type))

        self.meta.finalize()

        # apply recipe typing to expand var values

        # calculate recipe signature

        return


    def datahash(self):
        #import bb.data
        import hashlib

        if self._datahash:
            return self._datahash

        class StringOutput:
            def __init__(self):
                self.blob = ""
            def write(self, msg):
                self.blob += str(msg)
            def __len__(self):
                return len(self.blob)

        class StringHasher:
            def __init__(self, hasher):
                self.hasher = hasher
            def write(self, msg):
                self.hasher.update(str(msg))
            def __str__(self):
                return self.hasher.hexdigest()

        hasher = StringHasher(hashlib.md5())

        self.meta.dump(hasher, pretty=False, nohash=False)

        self._datahash = str(hasher)
        return self._datahash


    def srchash(self):
        if self._srchash:
            return self._srchash
