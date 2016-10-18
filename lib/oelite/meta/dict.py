from oelite.meta import *
import oelite.path

import sys
import copy
import warnings
import cPickle
import operator
import types
import os
import oelite.profiling

def deepcopy_str(x, memo):
    return intern(x)

copy._deepcopy_dispatch[str] = deepcopy_str


def unpickle(file):
    return DictMeta(meta=file)


class DictMeta(MetaData):


    def pickle(self, file):
        cPickle.dump(self.smpl, file, 2)
        cPickle.dump(self.cplx, file, 2)
        cPickle.dump(self.expand_cache, file, 2)
        cPickle.dump(self.__flag_index, file, 2)
        return


    INDEXED_FLAGS = {
        "python": 0,
        "task": 1,
        "autoimport": 2,
        "precondition": 3,
        "export": 4,
    }

    OVERRIDE_TYPE = {
        "": 0,
        ">": 1,
        "<": 2,
    }

    @oelite.profiling.profile_calls
    def __init__(self, meta=None):
        if isinstance(meta, file):
            self.smpl = copy.deepcopy(cPickle.load(meta))
            self.cplx = copy.deepcopy(cPickle.load(meta))
            self.expand_cache = copy.deepcopy(cPickle.load(meta))
            self.__flag_index = copy.deepcopy(cPickle.load(meta))
            meta = None
        elif isinstance(meta, DictMeta):
            self.smpl = copy.deepcopy(meta.smpl)
            self.cplx = copy.deepcopy(meta.cplx)
            self.expand_cache = meta.expand_cache.copy()
            self.__flag_index = copy.deepcopy(meta.__flag_index)
            meta = None
        else:
            self.smpl = {}
            self.cplx = {}
            self.expand_cache = {}
            self.__flag_index = [None] * len(self.INDEXED_FLAGS)
        self.expand_cache_filled = False
        super(DictMeta, self).__init__(meta=meta)
        return


    def copy(self):
        return DictMeta(meta=self)


    def __repr__(self):
        return '%s()'%(self.__class__.__name__)


    def __str__(self):
        return ",".join((str(self.smpl), str(self.cplx)))


    def __len__(self): # required by Sized
        return len(self.cplx) + len(self.smpl)


    def keys(self):
        # It's a bug if these two lists are not disjoint
        return self.cplx.keys() + self.smpl.keys()


    def set(self, var, val):
        assert not " " in var
        # If var is already a complex variable, just update its ""
        # member. Otherwise, this is (at least for now) a simple
        # variable.
        if var in self.cplx:
            self.cplx[var][""] = val
        else:
            self.smpl[var] = val
        self.trim_expand_cache(var)
        return


    def trim_expand_cache(self, var):
        for (cached_var, (cached_val, deps)) in self.expand_cache.items():
            if cached_var == var or (deps and var in deps):
                # FIXME: is it safe to delete from the dict we are iterating ?
                del self.expand_cache[cached_var]
        return


    def set_flag(self, var, flag, val):
        #print "set_flag %s[%s]=%s"%(var, flag, val)
        assert not " " in var

        if flag == "":
            self.set(var, val)
            return

        # Regardless of whether var exists in self.smpl, it is now a
        # complex variable. So start by setting the flag, creating
        # self.cplx[var] if it doesn't already exist.
        try:
            self.cplx[var][flag] = val
        except KeyError:
            self.cplx[var] = {flag: val}
            if var in self.smpl:
                # Carry over the simple value
                self.cplx[var][""] = self.smpl[var]
                del self.smpl[var]

        try:
            fidx = self.INDEXED_FLAGS[flag]
            if val:
                if self.__flag_index[fidx] is None:
                    self.__flag_index[fidx] = set([])
                self.__flag_index[fidx].add(var)
            else:
                if self.__flag_index[fidx]:
                    self.__flag_index[fidx].discard(var)
        except KeyError:
            pass

        return


    def weak_set_flag(self, var, flag, val):
        if var in self.cplx and flag in self.cplx[var]:
            pass
        else:
            # Either var is simple or doesn't exist at all. set_flag
            # will handle both these cases correctly.
            self.set_flag(var, flag, val)

    def set_override(self, var, override, val):
        assert var not in ("OVERRIDES", "__overrides", "", ">", "<")

        otype = self.OVERRIDE_TYPE[override[0]]

        if var in self.cplx:
            try:
                olist = self.cplx[var]["__overrides"]
            except KeyError:
                olist = self.cplx[var]["__overrides"] = [None, None, None]
        else:
            olist = [None, None, None]
            self.cplx[var] = {"__overrides": olist}

        if olist[otype] is None:
            olist[otype] = {}
        olist[otype][override[1]] = val

        if var in self.smpl:
            self.cplx[var][""] = self.smpl[var]
            del self.smpl[var]
        self.trim_expand_cache(var)
        return

    def get(self, var, expand=FULL_EXPANSION):
        #print "get var=%s expand=%s"%(var, expand)
        val = self._get(var, expand)[0]
        #print "get returning %s"%(val)
        return val


    def _get(self, var, expand=FULL_EXPANSION):
        #print "_get expand=%s"%(expand)
        assert isinstance(expand, int)
        try:
            val = self.smpl[var]
        except KeyError:
            try:
                val = self.cplx[var][""]
            except KeyError:
                try:
                    val = self.cplx[var]["defaultval"]
                except KeyError:
                    val = None
        if not expand:
            return (val, None)
        if not var in self.cplx and not var in self.smpl:
            return (None, None)
        if not isinstance(val, (basestring, types.NoneType)):
            return (val, None)
        if expand != OVERRIDES_EXPANSION:
            try:
                return self.expand_cache[var]
            except KeyError:
                pass

        override_dep = None
        if var in self.cplx and "__overrides" in self.cplx[var]:
            current_overrides, override_dep = self._get_overrides()
            if override_dep:
                override_dep.add("OVERRIDES")
            else:
                override_dep = set(["OVERRIDES"])
            olist = self.cplx[var]["__overrides"]
            var_overrides = olist[self.OVERRIDE_TYPE['']] or {}
            append_overrides = olist[self.OVERRIDE_TYPE['>']] or {}
            prepend_overrides = olist[self.OVERRIDE_TYPE['<']] or {}
            oval = None
            append = ""
            prepend = ""
            var_override_used = None
            overrides_used = set()
            for override in current_overrides:
                if oval is None:
                    try:
                        oval = var_overrides[override]
                        var_override_used = override
                    except KeyError:
                        pass
                try:
                    append += append_overrides[override] or ""
                    overrides_used.add(override)
                except KeyError:
                    pass
                try:
                    prepend = (prepend_overrides[override] or "") + prepend
                    overrides_used.add(override)
                except KeyError:
                    pass
            if oval is not None:
                val = oval
                overrides_used.add(var_override_used)
            val = prepend + (val or "") + append
            for override in overrides_used:
                if override.startswith('MACHINE_'):
                    self['EXTRA_ARCH'] = '.%s'%(self['MACHINE'])
                    break

        if expand == OVERRIDES_EXPANSION:
            return (val, None)

        deps = set()
        #print "get expanding %s=%s"%(var, repr(val))
        expand_method = self.get_flag(var, "expand")
        if expand_method:
            expand_method = int(expand_method)
        elif self.get_flag(var, "python"):
            expand_method = NO_EXPANSION
        else:
            #expand_method = FULL_EXPANSION
            expand_method = expand
        if val:
            #print "get not expanding anyway"
            self.expand_stack.push(var)
            (val, deps) = self._expand(val, expand_method, var)
            self.expand_stack.pop()

        if override_dep:
            deps = deps.union(override_dep)
        if not deps:
            deps = None
        self.expand_cache[var] = (val, deps)
        return (val, deps)

    def _fill_expand_cache(self):
        if self.expand_cache_filled:
            return
        for var in self.smpl:
            self._get(var)
        for var, val in self.cplx.iteritems():
            if "python" in val:
                continue
            self._get(var)
        self.expand_cache_filled = True

    def get_overrides(self):
        return _get_overrides(self)[0]

    def _get_overrides(self):
        overrides = self._get("OVERRIDES", PARTIAL_EXPANSION)
        filtered = []
        for override in overrides[0].split(":"):
            if not "${" in override:
                filtered.append(override)
        return (filtered, overrides[1])


    def get_flag(self, var, flag, expand=False):
        assert isinstance(expand, int)
        try:
            val = self.cplx[var][flag]
        except KeyError:
            if flag == "":
                val = self.smpl.get(var)
            else:
                val = None
        if val and expand:
            (val, deps) = self._expand(val, expand)
        return val


    def get_override(self, var, override):
        try:
            otype = self.OVERRIDE_TYPE[override[0]]
            return self.cplx[var]["__overrides"][otype][override[1]]
        except KeyError:
            # No var in cplx, no __overrides in cplx[var], or
            # override[1] not in the innermost dict
            pass
        except TypeError:
            # Morally, the dict at [otype] is empty, but we've used
            # None to save memory, so we get 'NoneType' object has no
            # attribute '__getitem__' instead of KeyError.
            pass
        return None

    def del_var(self, var):
        #print "del_var %s"%(var)
        for s in self.__flag_index:
            if s:
                s.discard(var)
        if var in self.cplx:
            del self.cplx[var]
        if var in self.smpl:
            del self.smpl[var]
        try:
            del self.expand_cache[var]
        except KeyError:
            pass
        return


    def get_list(self, var, expand=FULL_EXPANSION):
        return (self.get(var, expand) or "").split()


    def get_flag_list(self, var, flag, expand=False):
        return (self.get_flag(var, flag, expand) or "").split()


    def get_vars(self, flag="", values=False):
        #print "get_vars flag=%s values=%s"%(flag, values)
        if flag and not flag in self.INDEXED_FLAGS:
            print "get_vars flag=%s not indexed"%(flag)
            print "__flag_index=%s"%(self.__flag_index)
        if values:
            vars = {}
            if flag in self.INDEXED_FLAGS:
                fidx = self.INDEXED_FLAGS[flag]
                for var in self.__flag_index[fidx] or []:
                    try:
                        vars[var] = self.cplx[var][""]
                    except KeyError:
                        assert var not in self.smpl
                        continue
            else:
                for var in self.cplx:
                    try:
                        if flag is not None and not self.cplx[var][flag]:
                            continue
                        vars[var] = self.cplx[var][""]
                    except KeyError:
                        continue
                if flag == "":
                    vars.update(self.smpl)
        else:
            if flag in self.INDEXED_FLAGS:
                fidx = self.INDEXED_FLAGS[flag]
                vars = (self.__flag_index[fidx] or set([])).copy()
            else:
                vars = []
                for var in self.cplx:
                    try:
                        if flag is not None and not self.cplx[var][flag]:
                            continue
                        vars.append(var)
                    except KeyError:
                        continue
                if flag == "":
                    vars.extend(self.smpl.keys())
        #print "get_vars: %s"%(vars)
        return vars


    def get_flags(self, var, prune_var_value=True):
        try:
            flags = self.cplx[var].copy()
        except KeyError:
            try:
                flags = {"": self.smpl[var]}
            except KeyError:
                return None

        if prune_var_value:
            try:
                del flags[""]
            except KeyError:
                pass

        return flags


    def get_var_flags(self, flag="", append=()):
        var_flags = []
        for var in self.get_vars(flag):
            flags = self.get_flags(var, prune_var_value=False)
            for flag in flags:
                var_flags.append((var, flag, flags[flag]) + append)
        return var_flags


    def add_hook(self, name, function, sequence=1, after=[], before=[]):
        if after is None:
            after = []
        if before is None:
            before = []
        try:
            hooks = self.cplx["__hooks"]
        except KeyError:
            hooks = self.cplx["__hooks"] = {}
        try:
            functions = hooks[name]
        except KeyError:
            functions = hooks[name] = {}
        try:
            if sequence is None or sequence == functions[function][0]:
                functions[function] = (functions[function][0],
                                       functions[function][1].union(after))
            elif functions[function][0] is None:
                functions[function] = (sequence,
                                       functions[function][1].union(after))
            else:
                raise Exception("Invalid addhook statement (add more debug info here telling what sequence mismatch is and how to resolve it)")
        except KeyError:
            functions[function] = (sequence, set(after))
        for other_function in before:
            try:
                functions[other_function][1].add(function)
            except KeyError:
                functions[other_function] = (None, set([function]))
        self.weak_set_flag(function, "emit", "")
        return


    def get_hooks(self, name):
        try:
            functions = self.cplx["__hooks"][name]
        except KeyError:
            return []
        functions = sorted(functions.iteritems(), key=operator.itemgetter(1))
        num_functions = len(functions)
        i = 0
        while i < num_functions:
            moved = []
            function = functions[i][0]
            sequence = functions[i][1][0]
            after = list(functions[i][1][1])
            if not after:
                i += 1
                continue
            move_after = None
            for j in xrange(i+1, num_functions):
                if functions[j][0] in after:
                    move_after =  max(move_after, j)
            if not move_after:
                i += 1
                continue
            if function in moved:
                raise Exception(
                    "circular hook dependency detected: %s"%(function))
            del functions[i]
            functions.insert(move_after, (function, (sequence, after)))
            moved.append(function)
        return [function[0] for function in functions
                if function[1][0] is not None]


    def set_preference(self, packages=[], recipe=None,
                       layer=None, version=None):
        if packages:
            return self.set_preferred_packages(packages, recipe, layer, version)
        else:
            return self.set_preferred_recipe(recipe, layer, version)

    def set_preferred_recipe(self, recipe, layer, version):
        preferred_recipes = self.get('__preferred_recipes') or {}
        try:
            preferences = preferred_recipes[recipe]
        except KeyError:
            preferences = preferred_recipes[recipe] = []
        preferences.append((layer, version))
        self.set('__preferred_recipes', preferred_recipes)

    def set_preferred_packages(self, packages, recipe, layer, version):
        preferred_packages = self.get('__preferred_packages') or {}
        for package in packages:
            try:
                preferences = preferred_packages[package]
            except KeyError:
                preferences = preferred_packages[package] = []
            preferences.append((recipe, layer, version))
        self.set('__preferred_packages', preferred_packages)
        return


    def set_input_mtime(self, fn, path=None, mtime=None):
        if mtime is None:
            if path:
                f = oelite.path.which(path, fn)
                if f:
                    mtime = os.path.getmtime(f)
                else:
                    mtime = None
            elif os.path.exists(fn):
                mtime = os.path.getmtime(fn)
            else:
                mtime = None
        mtimes = self.get_input_mtimes()
        mtimes.append((fn, path, mtime))
        self.set("__mtimes", mtimes)
        return


    def get_input_mtimes(self):
        return self.get("__mtimes", expand=False) or []


    def finalize(self):
        #warnings.warn("FIXME: implement DictMeta.finalize()")
        return
