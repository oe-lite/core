#from oelite.meta import *
import oelite.meta
import oelite.recipe

import bb.utils

import os
import cPickle

class MetaCache:

    def __init__(self, cachefile, recipes=None, baker=None):
        if not recipes:
            try:
                self.file = open(cachefile)
                self.abi = cPickle.load(self.file)
                self.env_signature = cPickle.load(self.file)
                self.mtimes = cPickle.load(self.file)
            finally:
                return

        if os.path.exists(cachefile):
            os.unlink(cachefile)
        bb.utils.mkdirhier(os.path.dirname(cachefile))
        self.abi = pickle_abi()
        self.env_signature = baker.env_signature
        self.mtimes = set()
        self.meta = {}
        self.expand_cache = {}
        for type in recipes:
            for mtime in recipes[type].meta.get_input_mtimes():
                self.mtimes.add(mtime)
        self.file = open(cachefile, "w")
        cPickle.dump(self.abi, self.file, 2)
        cPickle.dump(self.env_signature, self.file, 2)
        cPickle.dump(self.mtimes, self.file, 2)
        cPickle.dump(len(recipes), self.file, 2)
        for type in recipes:
            recipes[type].pickle(self.file)
        return


    def is_current(self, baker):
        try:
            if pickle_abi() != self.abi:
                return False
            if baker.env_signature != self.env_signature:
                return False
            if not isinstance(self.mtimes, set):
                return False
        except AttributeError:
            return False
        for (fn, oepath, old_mtime) in list(self.mtimes):
            filepath = bb.utils.which(oepath, fn)
            if os.path.exists(filepath):
                cur_mtime = os.path.getmtime(filepath)
            else:
                cur_mtime = None
            if cur_mtime != old_mtime:
                return False
        return True


    def load(self, filename, cookbook):
        recipes = {}
        for i in xrange(cPickle.load(self.file)):
            recipe = oelite.recipe.unpickle(
                self.file, filename, cookbook)
            recipes[recipe.type] = recipe
        return recipes


    def __repr__(self):
        return '%s()'%(self.__class__.__name__)


    def __iter__(self):
        return self.meta.keys().__iter__()


PICKLE_ABI = None

def pickle_abi():
    global PICKLE_ABI
    if not PICKLE_ABI:
        import inspect
        import hashlib
        import oelite.meta
        import oelite.parse
        srcfiles = [__file__,
                    oelite.meta.__file__,
                    inspect.getsourcefile(oelite.meta.MetaData),
                    inspect.getsourcefile(oelite.meta.DictMeta),
                    oelite.parse.oelex.__file__,
                    oelite.parse.oeparse.__file__,
                    oelite.parse.confparse.__file__,
                    inspect.getsourcefile(oelite.fetch),
                    inspect.getsourcefile(oelite.fetch.fetch),
                    inspect.getsourcefile(oelite.fetch.local),
                    inspect.getsourcefile(oelite.fetch.url),
                    inspect.getsourcefile(oelite.fetch.sigfile),
                    inspect.getsourcefile(oelite.fetch.git),
                    inspect.getsourcefile(oelite.fetch.hg),
                    ]
        m = hashlib.md5()
        for srcfile in srcfiles:
            with open(srcfile) as _srcfile:
                m.update(_srcfile.read())
        PICKLE_ABI = m.digest()
    return PICKLE_ABI
