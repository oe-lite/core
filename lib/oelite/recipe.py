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
        self.priority = self.meta.get("DEFAULT_PREFERENCE") or "0"
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
        #return flatten_single_column_rows(self.cookbook.dbc.execute(
        #    "SELECT item FROM recipe_depend WHERE recipe=?", (self.id,)))
        return self.meta.get_list("DEPENDS")

    def get_rdepends(self):
        #return flatten_single_column_rows(self.dbc.execute(
        #    "SELECT item FROM recipe_rdepend WHERE recipe=?", (self.id,)))
        return self.meta.get_list("RDEPENDS")


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


    def prepare(self, runq, task):

        meta = self.meta.copy()

        buildhash = self.cookbook.baker.runq.get_task_buildhash(task)
        debug("buildhash=%s"%(repr(buildhash)))
        meta.setVar("TASK_BUILDHASH", buildhash)

        deploy_dir = meta.getVar("PACKAGE_DEPLOY_DIR", True) 

        recipe_type = meta.getVar("RECIPE_TYPE", False)
        
        if recipe_type == "canadian-cross":
            host_arch = meta.getVar("HOST_ARCH", True)

        def set_pkgproviders(get_depend_packages,
                             PKGPROVIDER_, RECDEPENDS):
            recdepends = []

            packages = get_depend_packages(task) or []
            for package in packages:
                if package in recdepends:
                    continue

                (package_name, package_arch) = self.db.get_package(package)
                filename = self.cookbook.baker.runq.get_package_filename(package)
                recdepends.append(package_name)
                debug("setting %s%s=%s"%(
                        PKGPROVIDER_, package_name, filename))
                meta.setVar(PKGPROVIDER_ + package_name, filename)

                if package_arch.startswith("native/"):
                    subdir = "native"
                else:
                    subdir = package_arch.split("/", 1)[0]
                    if recipe_type == "canadian-cross":
                        if package_arch == "cross/%s"%(host_arch):
                            subdir = os.path.join("host", subdir)
                        elif package_arch == "sysroot/%s"%(host_arch):
                            subdir = os.path.join("host", subdir)
                        elif package_arch.startswith("sysroot/%s--"%(host_arch)):
                            subdir = os.path.join("host", subdir)
                        else:
                            subdir = os.path.join("target", subdir)
                meta.setVar("PKGSUBDIR_" + package_name, subdir)

            if recdepends:
                debug("setting %s=%s"%(RECDEPENDS, " ".join(recdepends)))
            warnings.warn("save to __stage and __rstage instead of RECDEPENDS and RECRDEPENDS and PKGPROVIDER_* and PKGRPROVIDER_* (and set nohash flag for them).  The __stage and __rstage variables can a proper Python structured variable, to simplify the do_stage and do_rstage variables")
            meta.setVar(RECDEPENDS, " ".join(recdepends))

        set_pkgproviders(self.cookbook.baker.runq.get_depend_packages,
                         "PKGPROVIDER_", "RECDEPENDS")

        set_pkgproviders(self.cookbook.baker.runq.get_rdepend_packages,
                         "PKGRPROVIDER_", "RECRDEPENDS")

        return meta


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
