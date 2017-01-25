from oebakery import die, err, warn, info, debug
from oelite import InvalidRecipe
import oelite.meta
from oelite.dbutil import *

import sys
import os
import cPickle
import warnings
import shutil

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
        self.layer_priority = int(self.meta.get("LAYER_PRIORITY"))
        self.priority_baseline = int(self.meta.get("PRIORITY_BASELINE"))
        priority = self.meta.get("PRIORITY")
        if priority is None:
            priority = self.meta.get("DEFAULT_PREFERENCE")
        priority = int(priority)
        self.priority = self.layer_priority + self.priority_baseline + priority
        self._datahash = None
        self._hash = None
        self.recipe_deps = set([])
        self.tasks = set([])
        self.item_deps = {}
        for deptype in ("DEPENDS", "RDEPENDS", "FDEPENDS"):
            # (type, itemname) => version
            self.item_deps[deptype] = set()
        self.rmwork = False
        return


    def __str__(self):
        return "%s:%s_%s"%(self.type, self.name, self.version)

    def set_id(self, id):
        self.id = id
        return

    def get(self, var):
        return self.meta.get(var)

    def set(self, var, val):
        return self.meta.set(var, val)

    def get_flag(self, var, flag):
        return self.meta.get_flag(var, flag)

    def get_task_names(self):
        return self.meta.get_vars(flag="task")

    def get_packages(self):
        return self.cookbook.get_packages(recipe=self)

    def get_depends(self, deptypes=[]):
        depends = []
        if not deptypes:
            deptypes = self.item_deps.keys()
        for t in deptypes:
            for item in self.item_deps[t]:
                depends.append(str(item))
        return depends


    def add_task(self, task, task_deps):
        self.tasks.add(task)
        for task_dep in task_deps:
            if task_dep.recipe == self:
                continue
            self.recipe_deps.add(task_dep.recipe)
        return


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
        preference = self.meta.get("DEFAULT_PREFERENCE") or "0"
        try:
            preference = int(preference)
        except ValueError, e:
            raise InvalidRecipe("invalid DEFAULT_PREFERENCE=%s in %s:%s"%(
                    preference, filename, recipe_type))

        self.meta.finalize()

        # apply recipe typing to expand var values

        # calculate recipe signature

        return


    def is_cacheable(self):
        dont_cache = self.get("__dont_cache")
        if dont_cache and dont_cache != "0":
            return False
        return True

    def do_rmwork(self):
        if not self.rmwork:
            return

        workdir = self.meta.get("WORKDIR")
        if not workdir:
            print "ERROR: rmwork %s: WORKDIR not set" % self
            return
        stampdir = self.meta.get("STAMPDIR")
        if not stampdir:
            print "ERROR: rmwork %s: STAMPDIR not set" % self
            return
        dirs = (self.meta.get("RMWORK_DIRS") or "").split()
        try:
            shutil.rmtree(stampdir)
            for d in dirs:
                if not (d == workdir or d.startswith(workdir + "/")):
                    # We should probably canonicalize the paths before
                    # the comparison, but this is 99% good enough.
                    print "INFO: rmwork %s: skipping %s, not a subdirectory of ${WORKDIR}" % (self, d)
                    continue
                if not os.path.isdir(d):
                    # No diagnostic, we may just have removed the same
                    # directory or a parent already (e.g. when B==S),
                    # or the directory not be applicable to this
                    # recipe (e.g. IMAGE_DIR).
                    continue
                shutil.rmtree(d)

        except Exception as e:
            print "ERROR: rmwork %s: exception %s" % (self, e)
