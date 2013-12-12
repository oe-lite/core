from oelite.meta import *
import oelite.path

import sys
import copy
import warnings
import cPickle
import operator
import types
import os


def unpickle(file):
    return DictMeta(meta=file)


class DictMeta(MetaData):


    def pickle(self, file):
        cPickle.dump(self.dict, file, 2)
        cPickle.dump(self.expand_cache, file, 2)
        return


    INDEXED_FLAGS = ("python", "task", "autoimport", "precondition", "export")


    def __init__(self, meta=None):
        if isinstance(meta, file):
            self.dict = cPickle.load(meta)
            self.expand_cache = cPickle.load(meta)
            meta = None
        elif isinstance(meta, DictMeta):
            self.dict = {}
            #self.dict = meta.dict.copy()
            self.dict = copy.deepcopy(meta.dict)
            #for var in meta.dict:
            #    self.dict[var] = meta.dict[var].copy()
            self.expand_cache = meta.expand_cache.copy()
            #self.expand_cache = copy.deepcopy(meta.expand_cache)
            meta = None
        elif isinstance(meta, dict):
            self.dict = meta
            self.expand_cache = {}
            meta = None
        else:
            self.dict = {}
            self.expand_cache = {}
            self.dict["__flag_index"] = {}
            for flag in self.INDEXED_FLAGS:
                self.dict["__flag_index"][flag] = set([])
        super(DictMeta, self).__init__(meta=meta)
        return


    def copy(self):
        return DictMeta(meta=self)


    def __repr__(self):
        return '%s()'%(self.__class__.__name__)


    def __str__(self):
        return str(self.dict)


    def __len__(self): # required by Sized
        return len(self.dict)


    def keys(self):
        return self.dict.keys()


    def set(self, var, val):
        assert not " " in var
        try:
            self.dict[var][""] = val
        except KeyError:
            self.dict[var] = {"": val}
        self.trim_expand_cache(var)
        return


    def trim_expand_cache(self, var):
        for (cached_var, (cached_val, deps)) in self.expand_cache.items():
            if cached_var == var or var in deps:
                del self.expand_cache[cached_var]
        return


    def set_flag(self, var, flag, val):
        #print "set_flag %s[%s]=%s"%(var, flag, val)
        assert not " " in var
        try:
            self.dict[var][flag] = val
        except KeyError:
            self.dict[var] = {flag: val}
        if hasattr(self.dict, '__flag_index'):
            if flag in self.dict["__flag_index"]:
                if val:
                    self.dict["__flag_index"][flag].add(var)
                else:
                    self.dict["__flag_index"][flag].discard(var)
        if flag == "":
            self.trim_expand_cache(var)
        return


    def weak_set_flag(self, var, flag, val):
        if not var in self.dict.keys() or not flag in self.dict[var].keys():
            self.set_flag(var, flag, val)


    def set_override(self, var, override, val):
        assert var not in ("OVERRIDES", "__overrides", "", ">", "<")
        assert override[0] in ("", ">", "<")
        try:
            self.dict[var]["__overrides"][override[0]][override[1]] = val
        except KeyError, e:
            if e.args[0] == var:
                self.dict[var] = {"__overrides": {'':{}, '>':{}, '<':{}}}
            else:
                assert e.args[0] == "__overrides"
                self.dict[var]["__overrides"] = {'':{}, '>':{}, '<':{}}
            self.dict[var]["__overrides"][override[0]][override[1]] = val
        self.trim_expand_cache(var)
        return


    def get(self, var, expand=FULL_EXPANSION):
        #print "get var=%s expand=%s"%(var, expand)
        assert isinstance(expand, int)
        val = self._get(var, expand)[0]
        #print "get returning %s"%(val)
        return val


    def _get(self, var, expand=FULL_EXPANSION):
        #print "_get expand=%s"%(expand)
        assert isinstance(expand, int)
        try:
            val = self.dict[var][""]
        except KeyError:
            try:
                val = self.dict[var]["defaultval"]
            except KeyError:
                val = None
        if not expand:
            return (val, None)
        if not var in self.dict:
            return (None, None)
        if not isinstance(val, (basestring, types.NoneType)):
            return (val, None)
        if expand != OVERRIDES_EXPANSION:
            try:
                return self.expand_cache[var]
            except KeyError:
                pass

        override_dep = None
        if "__overrides" in self.dict[var]:
            current_overrides, override_dep = self._get_overrides()
            override_dep.add("OVERRIDES")
            var_overrides = self.dict[var]["__overrides"]['']
            append_overrides = self.dict[var]["__overrides"]['>']
            prepend_overrides = self.dict[var]["__overrides"]['<']
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
            self.expand_stack.push("${%s}"%var)
            (val, deps) = self._expand(val, expand_method, var)
            self.expand_stack.pop()

        if override_dep:
            deps = deps.union(override_dep)
        self.expand_cache[var] = (val, deps)
        return (val, deps)


    def get_overrides(self):
        return _get_overrides(self)[0]

    def _get_overrides(self):
        overrides = self._get("OVERRIDES", 2)
        filtered = []
        for override in overrides[0].split(":"):
            if not "${" in override:
                filtered.append(override)
        return (filtered, overrides[1])


    def get_flag(self, var, flag, expand=False):
        assert isinstance(expand, int)
        try:
            val = self.dict[var][flag]
        except KeyError:
            val = None
        if val and expand:
            (val, deps) = self._expand(val, expand)
        return val


    def get_override(self, var, override):
        try:
            return self.dict[var]["__overrides"][override[0]][override[1]]
        except KeyError:
            pass
        return None

    def del_var(self, var):
        if hasattr(self.dict, '__flag_index'):
            for flag in self.dict['__flag_index']:
                self.dict['__flag_index'][flag].discard(var)
        del self.dict[var]
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
        if (flag and
            hasattr(self.dict, '__flag_index') and
            not flag in self.dict['__flag_index']):
            print "get_vars flag=%s not indexed"%(flag)
            print "__flag_index=%s"%(self.dict['__flag_index'])
        if values:
            vars = {}
            if (hasattr(self.dict, '__flag_index') and
                flag in self.dict['__flag_index']):
                for var in self.dict['__flag_index'][flag]:
                    try:
                        vars[var] = self.dict[var][""]
                    except KeyError:
                        continue
            else:
                for var in self.dict:
                    try:
                        if flag is not None and not self.dict[var][flag]:
                            continue
                        vars[var] = self.dict[var][""]
                    except KeyError:
                        continue
        else:
            if (hasattr(self.dict, '__flag_index') and
                flag in self.dict['__flag_index']):
                vars = self.dict['__flag_index'][flag].copy()
            else:
                vars = []
                for var in self.dict:
                    try:
                        if flag is not None and not self.dict[var][flag]:
                            continue
                        vars.append(var)
                    except KeyError:
                        continue
        #print "get_vars: %s"%(vars)
        return vars


    def get_flags(self, var, prune_var_value=True):
        try:
            flags = self.dict[var].copy()
            if prune_var_value:
                try:
                    del flags[""]
                except KeyError:
                    pass
        except KeyError:
            return None
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
            hooks = self.dict["__hooks"]
        except KeyError:
            hooks = self.dict["__hooks"] = {}
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
            functions = self.dict["__hooks"][name]
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
