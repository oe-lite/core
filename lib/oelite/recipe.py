from oebakery import die, err, warn, info, debug
from oelite import InvalidRecipe
import oelite.meta
import oelite.process
from oelite.dbutil import *
from oelite.log import log

import sys
import os
import re
import cPickle
import warnings


def unpickle(file, filename, cookbook):
    type = cPickle.load(file)
    meta = oelite.meta.dict.unpickle(file)
    return OEliteRecipe(filename, type, meta, cookbook)


class OEliteRecipe:

    PRELOAD_VARS = (
        'RECIPE_TYPE', 'PN', 'PV', 'DEFAULT_PREFERENCE', 'PACKAGES',
        'RECIPE_ARCH', 'REBUILD', 'REBUILDALL_SKIP', 'RELAXED',
        'DEPENDS', 'CLASS_DEPENDS', 'RDEPENDS', 'CLASS_RDEPENDS',
        'FDEPENDS', 'CLASS_FDEPENDS',
        'HOOKTMPDIR', 'STAMPDIR', 'OE_IMPORTS',
        )
    PRELOAD_PACKAGE_VARS = re.compile('^(%s)_'%('|'.join(
                ('PACKAGE_ARCH', 'PACKAGE_TYPE',
                 'PROVIDES', 'DEPENDS', 'RDEPENDS'))))
    PRELOAD_VARS_WITH_FLAG = ('task', 'precondition')

    @classmethod
    def pickle(cls, file, token, meta):
        preload_meta = {}
        for var in meta.dict.keys():
            if var in cls.PRELOAD_VARS or cls.PRELOAD_PACKAGE_VARS.match(var):
                preload_meta[var] = { '': meta.get(var) }
        preload_vars = set()
        for flag in cls.PRELOAD_VARS_WITH_FLAG:
            preload_vars.update(meta.get_vars(flag=flag))
        for var in preload_vars:
            preload_meta[var] = meta.dict[var]
        preload_meta = oelite.meta.dict.DictMeta(meta=preload_meta)
        cPickle.dump(token, file)
        preload_meta.pickle(file)
        meta.pickle(file)
        return

    def __init__(self, cache, recipe_type, cookbook):
        self.filename = cache.recipe_file
        self.type = recipe_type
        self.cookbook = cookbook
        self.meta_cache = cache.meta_cache(recipe_type)
        with open(self.meta_cache, 'r') as meta_cache:
            self.token = cPickle.load(meta_cache)
            # preload metadata
            self.meta = oelite.meta.dict.DictMeta(meta=meta_cache)
            # save offset to full metadata
            self.meta_cache_offset = meta_cache.tell()
        self.name = self.meta.get("PN")
        self.version = self.meta.get("PV")
        self.priority = int(self.meta.get("DEFAULT_PREFERENCE") or "0")
        self._datahash = None
        self._hash = None
        self.recipe_deps = set([])
        self.tasks = set([])
        return

    def load_meta(self):
        with open(self.meta_cache, 'r') as meta_cache:
            token = cPickle.load(meta_cache)
            assert token == self.token
            meta_cache.seek(self.meta_cache_offset)
            self.meta = oelite.meta.dict.DictMeta(meta=meta_cache)
        return

    # the following information is needed to add recipe to cookbook:
    # Common:
    #   filename
    #   recipe_types
    # Recipe type specific:
    #   type
    #   name
    #   version
    #   priority
    #   get_task_names()
    #   meta.get DEPENDS, RDEPENDS, FDEPENDS and the CLASS_*DEPENDS
    #   for task_name in tasks:
    #     recipe.meta.get_boolean_flag(task_name, "nostamp")
    #     recipe.meta.get_list_flag(task_name, "deps")
    #     recipe.meta.get_list_flag(task_name, "deptask")
    #     recipe.meta.get_list_flag(task_name, "recdeptask")
    #     recipe.meta.get_list_flag(task_name, "depends")
    #   PACKAGES
    #   for package in PACKAGES:
    #     recipe.meta.get("PACKAGE_ARCH_" + package) or RECIPE_ARCH_*
    #     recipe.meta.get("PACKAGE_TYPE_" + package) or RECIPE_ARCH_*
    #     recipe.meta.get("PROVIDES_" + package)
    #     recipe.meta.get("DEPENDS_" + package)
    #     recipe.meta.get("RDEPENDS_" + package)
    #   REBUILD and REBUILDALL_SKIP
    #   RELEAXED
    #   recipe.get_depends()

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
        if deptypes:
            deptypes_in = " AND deptype IN (%s)"%(
                ",".join("?" for i in deptypes))
        else:
            deptypes_in = ""
        for type, item, version in self.cookbook.dbc.execute(
            "SELECT type, item, version FROM recipe_depend "
            "WHERE recipe_depend.recipe=?%s"%(deptypes_in),
            ([self.id] + deptypes)):
            if version is None:
                depends.append("%s:%s"%(type, item))
            else:
                depends.append("%s:%s_%s"%(type, item, version))
        return depends


    def add_task(self, task, task_deps):
        self.tasks.add(task)
        for task_dep in task_deps:
            if task_dep.recipe == self:
                continue
            self.recipe_deps.add(task_dep.recipe)
        return


    def get_cache(self):
        if not hasattr(self, 'cache'):
            self.cache = oelite.meta.cache.MetaCache(self.cookbook.config, self)
        return self.cache


class RecipeParser(oelite.process.PythonProcess):

    def __init__(self, cookbook, recipe_file, process=False):
        if process:
            self.recipe_meta = cookbook.config
        else:
            self.recipe_meta = cookbook.config.copy()
        self.oeparser = cookbook.oeparser
        self.recipe_file = recipe_file
        self.cache = oelite.meta.cache.MetaCache(cookbook.config, recipe_file)
        self.env_signature = cookbook.config.env_signature()
        self.session_signature = cookbook.session_signature
        tmpfile = os.path.join(cookbook.config.get('PARSERDIR'),
                               oelite.path.relpath(recipe_file))
        stdout = tmpfile + '.log'
        ipc = tmpfile + '.ipc'
        super(RecipeParser, self).__init__(
            stdout=stdout, ipc=ipc, target=self._parse)
        return

    def _parse(self):
        retval = self.parse()
        if not hasattr(self, 'feedback'):
            return retval
        if retval:
            self.feedback.error("Parsing failed: %s"%(retval))
            assert isinstance(retval, int)
            sys.exit(retval)
        else:
            self.feedback.progress(100)
            sys.exit(0)

    def parse(self):
        log.debug("Parsing %s", self.recipe_file)
        oelite.pyexec.exechooks(self.recipe_meta, "pre_recipe_parse")
        self.oeparser.set_metadata(self.recipe_meta)
        self.oeparser.reset_lexstate()
        try:
            self.recipe_meta = self.oeparser.parse(
                os.path.abspath(self.recipe_file))
        except oelite.parse.ParseError as e:
            e.print_details()
            sys.exit(1)
        oelite.pyexec.exechooks(self.recipe_meta, "mid_recipe_parse")
        recipe_types = (self.recipe_meta.get("RECIPE_TYPES") or "").split()
        if not recipe_types:
            recipe_types = ["machine"]
        self.meta = {}
        for recipe_type in recipe_types:
            self.meta[recipe_type] = self.recipe_meta.copy()
        for recipe_type in recipe_types:
            self.meta[recipe_type]["RECIPE_TYPE"] = recipe_type
            self.oeparser.set_metadata(self.meta[recipe_type])
            try:
                self.oeparser.parse("classes/type/%s.oeclass"%(recipe_type))
            except oelite.parse.ParseError as e:
                e.print_details()
                sys.exit(1)
            def arch_is_compatible(meta, arch_type):
                compatible_archs = meta.get("COMPATIBLE_%s_ARCHS"%arch_type)
                if compatible_archs is None:
                    return True
                arch = meta.get(arch_type + "_ARCH")
                for compatible_arch in compatible_archs.split():
                    if re.match(compatible_arch, arch):
                        return True
                debug("skipping %s_ARCH incompatible recipe %s:%s"%(
                    arch_type, recipe_type, meta.get("PN")))
                return False
            def cpu_families_is_compatible(meta, arch_type):
                compatible_cpu_fams = meta.get("COMPATIBLE_%s_CPU_FAMILIES"%arch_type)
                if compatible_cpu_fams is None:
                    return True
                cpu_fams = meta.get(arch_type + "_CPU_FAMILIES")
                if not cpu_fams:
                    return False
                for compatible_cpu_fam in compatible_cpu_fams.split():
                    for cpu_fam in cpu_fams.split():
                        if re.match(compatible_cpu_fam, cpu_fam):
                            return True
                debug("skipping %s_CPU_FAMILIES incompatible recipe %s:%s"%(
                    arch_type, recipe_type, meta.get("PN")))
                return False
            def machine_is_compatible(meta):
                compatible_machines = meta.get("COMPATIBLE_MACHINES")
                if compatible_machines is None:
                    return True
                machine = meta.get("MACHINE")
                if machine is None:
                    debug("skipping MACHINE incompatible recipe %s:%s"%(
                        recipe_type, meta.get("PN")))
                    return False
                for compatible_machine in compatible_machines.split():
                    if re.match(compatible_machine, machine):
                        return True
                debug("skipping MACHINE incompatible recipe %s:%s"%(
                    recipe_type, meta.get("PN")))
                return False
            def recipe_is_compatible(meta):
                incompatible_recipes = meta.get("INCOMPATIBLE_RECIPES")
                if incompatible_recipes is None:
                    return True
                pn = meta.get("PN")
                pv = meta.get("PV")
                for incompatible_recipe in incompatible_recipes.split():
                    if "_" in incompatible_recipe:
                        incompatible_recipe = incompatible_recipe.rsplit("_", 1)
                    else:
                        incompatible_recipe = (incompatible_recipe, None)
                    if not re.match("%s$"%(incompatible_recipe[0]), pn):
                        continue
                    if incompatible_recipe[1] is None:
                        return False
                    if re.match("%s$"%(incompatible_recipe[1]), pv):
                        debug("skipping incompatible recipe %s:%s_%s"%(
                            recipe_type, pn, pv))
                        return False
                return True
            def compatible_use_flags(meta):
                flags = meta.get("COMPATIBLE_IF_FLAGS")
                if not flags:
                    return True
                for name in flags.split():
                    val = meta.get("USE_"+name)
                    if not val:
                        debug("skipping %s:%s_%s (required %s USE flag not set)"%(
                                recipe_type, meta.get("PN"), meta.get("PV"),
                                name))
                        return False
                return True
            if ((not recipe_is_compatible(self.meta[recipe_type])) or
                (not machine_is_compatible(self.meta[recipe_type])) or
                (not arch_is_compatible(self.meta[recipe_type], "BUILD")) or
                (not arch_is_compatible(self.meta[recipe_type], "HOST")) or
                (not arch_is_compatible(self.meta[recipe_type], "TARGET"))):
                del self.meta[recipe_type]
                continue
            try:
                oelite.pyexec.exechooks(self.meta[recipe_type], "post_recipe_parse")
            except oelite.HookFailed, e:
                log.error("%s:%s %s post_recipe_parse hook: %s",
                          recipe_type, self.meta[''].get("PN"),
                          e.function, e.retval)
                return False
            if ((not compatible_use_flags(self.meta[recipe_type])) or
                (not cpu_families_is_compatible(
                        self.meta[recipe_type], "BUILD")) or
                (not cpu_families_is_compatible(
                        self.meta[recipe_type], "HOST")) or
                (not cpu_families_is_compatible(
                        self.meta[recipe_type], "TARGET"))):
                del meta[recipe_type]
                continue
        def is_cacheable(meta):
            for m in meta.values():
                if not m.is_cacheable():
                    return False
            return True
        if is_cacheable(self.meta):
            self.cache.save(self.env_signature, self.meta)
        else:
            self.cache.save(self.session_signature, self.meta)
        return
