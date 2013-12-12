import oelite.recipe
import oelite.util
import oelite.log
import oelite.path

import os
import cPickle
import random

log = oelite.log.get_logger()


class MetaCache:

    """Object representing a cache of a parsed OE-lite recipe.

    Each cache can only hold different types of the same recipes.  If a recipe
    file defines both a 'native' and 'machine' type recipe, a single cache
    should be used for holding both of these recipes.  For recipes from
    different recipe files, separate caches must be used.

    A cache consists of multiple files. One file is used for some
    generic recipe information, recipe metadata is stored in a
    separate file for each recipe type, and task metadata is stored in
    a separate file for each recipe type and task.  This is done to
    make it simple to efficiently load only what is needed.

    """

    ATTRIBUTES = (
         'token', 'src_signature', 'env_signature', 'mtimes', 'recipe_types')

    def __init__(self, config, recipe):
        """Constructor for OE-lite metadata cache files.

        Arguments:
        config -- configuration metadata.
        recipe -- path to the recipe file or OEliteRecipe instance.

        """
        if isinstance(recipe, oelite.recipe.OEliteRecipe):
            self.recipe_file = recipe.filename
        else:
            self.recipe_file = recipe
        self.path = os.path.join(
            config.get('PARSERDIR'),
            oelite.path.relpath(self.recipe_file) + ".cache")

    def __repr__(self):
        return '%s()'%(self.__class__.__name__)

    def meta_cache(self, recipe_type):
        """Get filename of recipe metadata cache file."""
        return '%s.%s'%(self.path, recipe_type)

    def task_cache(self, task):
        """Get filename of task cache file."""
        return '%s.%s.%s'%(self.path, task.recipe.type, task.name)

    def exists(self):
        """Check if cache file exists.

        Return True if underlying cache file exists, False otherwise.

        """
        return os.path.exists(self.path)

    def is_current(self, env_signatures):
        """Check if cache exists and is current.

        Arguments:
        env_signatures -- list of signatures to consider as current.

        Return True if recipe or task cache file exists and is
        current. Current state is determined based on source signature,
        environment signature, and mtime of recipe input files.

        """
        if not self.exists():
            return False
        if not self.load():
            return False
        try:
            if src_signature() != self.src_signature:
                return False
            if not self.env_signature in env_signatures:
                return False
            if not isinstance(self.mtimes, set):
                return False
        except AttributeError:
            return False
        for (fn, oepath, old_mtime) in list(self.mtimes):
            if oepath is not None:
                filepath = oelite.path.which(oepath, fn)
            else:
                assert os.path.isabs(fn)
                filepath = fn
            if os.path.exists(filepath):
                cur_mtime = os.path.getmtime(filepath)
            else:
                cur_mtime = None
            if cur_mtime != old_mtime:
                return False
        return True

    def has_meta(self, recipe_type):
        """Check if cache has valid recipe metadata cache file."""
        if not self.load():
            return False
        meta_cache = self.meta_cache(recipe_type)
        if not os.path.exists(meta_cache):
            return False
        with open(meta_cache, 'r') as cache_file:
            token = cPickle.load(cache_file)
            if token == self.token:
                return True
        return False

    def has_task(self, task):
        """Check if cache has valid task cache file."""
        if not self.load():
            return False
        task_cache = self.task_cache(task)
        if not os.path.exists(task_cache):
            return False
        with open(task_cache, 'r') as cache_file:
            token = cPickle.load(cache_file)
            if token == self.token:
                return True
        return False

    def clean(self):
        """Remove the underlying cache file (if it exists)."""
        if self.exists():
            log.debug("Removing stale metadata cache: %s", self.path)
            os.remove(self.path)
        # FIXME: rewrite to use glob.glob to remote task cache files also
        return

    def load(self):
        """Load the common recipe attributes from cache."""
        if getattr(self, '_loaded', False):
            for attr in self.ATTRIBUTES:
                assert hasattr(self, attr)
            return True
        try:
            cache_file = open(self.path)
        except:
            return False
        try:
            for attr in self.ATTRIBUTES:
                setattr(self, attr, cPickle.load(cache_file))
        except Exception as e:
            for attr in self.ATTRIBUTES:
                if hasattr(self, attr):
                    delattr(self, attr)
            return False
        finally:
            cache_file.close()
        self._loaded = True
        return True

    def load_recipes(self, cookbook=None, meta=True):
        """Load OE-lite recipe metadata from cache file and add to cookbook.

        Arguments:
        cookbook - oelite.cookbook.CookBook instance to create the recipe in.

        """
        # change to not actually load the recipe metadata, but just
        # all the stuff needed for adding to cookbook.
        # the recipe class must be changed to support being created without
        # the full metadata, and then load this later (on demand) from
        # the cache file
        if not self.load():
            return None
        recipes = {}
        for recipe_type in self.recipe_types:
            recipes[recipe_type] = oelite.recipe.OEliteRecipe(
                self, recipe_type, cookbook)
        return recipes

    def load_task(self, task, meta=True):
        """Load OE-lite task metadata from cache file.

        Arguments:
        task - oelite.task.OEliteTask instance to load.

        """
        if not self.load():
            return False
        task_cache = self.task_cache(task)
        with open(task_cache, 'r') as cache_file:
            token = cPickle.load(cache_file)
            if token != self.token:
                return None
            task.load_summary(cache_file)
            task.meta_cache_offset = cache_file.tell()
            if meta:
                task.load_meta(cache_file)
            else:
                task.meta_cache = task_cache
        return True

    def save(self, env_signature, recipes):
        """Save OE-lite metadata recipes to cache file.

        Arguments:
        env_signature -- environment variable signature.
        recipes -- dictionary of recipes to put in cache, indexed by recipe
            type as key (ie. 'native', 'machine', and so on), and values of
            type oelite.MetaData.

        """
        self.src_signature = src_signature()
        self.env_signature = env_signature
        mtimes = set()
        for type in recipes:
            for mtime in recipes[type].get_input_mtimes():
                mtimes.add(mtime)
        self.mtimes = mtimes
        self.token = '%032x'%(random.getrandbits(128))
        self.recipe_types = recipes.keys()
        oelite.util.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as cache_file:
            for attr in self.ATTRIBUTES:
                cPickle.dump(getattr(self, attr), cache_file, 2)
        for recipe_type in self.recipe_types:
            with open('%s.%s'%(self.path, recipe_type), "w") as cache_file:
                oelite.recipe.OEliteRecipe.pickle(
                    cache_file, self.token, recipes[recipe_type])
        return

    def save_task(self, task):
        """Save OE-lite task metadata to cache file.

        Arguments:
        task - oelite.task.OEliteTask instance to save.

        """
        if self.load():
            token = self.token
        else:
            token = ''
        with open(self.task_cache(task), 'w') as cache_file:
            cPickle.dump(token, cache_file, 2)
            task.save(cache_file, token)
        return


SRC_MODULES = [
    "oelite.meta",
    "oelite.meta.meta",
    "oelite.meta.dict",
    "oelite.meta.cache",
    "oelite.parse",
    "oelite.parse.oelex",
    "oelite.parse.oeparse",
    "oelite.parse.confparse",
    "oelite.parse.expandlex",
    "oelite.parse.expandparse",
    "oelite.fetch",
    "oelite.fetch.fetch",
    "oelite.fetch.sigfile",
    "oelite.fetch.local",
    "oelite.fetch.url",
    "oelite.fetch.git",
    "oelite.fetch.svn",
    "oelite.fetch.hg",
    "oelite",
    "oelite.arch",
    "oelite.baker",
    "oelite.cookbook",
    "oelite.dbutil",
    "oelite.function",
    "oelite.item",
    "oelite.package",
    "oelite.pyexec",
    "oelite.recipe",
    "oelite.runq",
    "oelite.task",
    "oelite.util",
    "oelite.meta",
    "oelite.meta.cache",
    ]


def src_signature():
    """Return hash signature of all source modules.

    Return message digest of source files for all Python modules in
    SRC_MODULES. The return value is a string which may contain non-ASCII
    characters, including null bytes.

    The digest is only generated once. All following calls to src_digest()
    returns a cached value.

    """
    global _src_digest
    if _src_digest:
        return _src_digest
    import inspect
    import hashlib
    files = []
    for module in SRC_MODULES:
        exec "import %s"%(module)
        files.append(inspect.getsourcefile(eval(module)))
    m = hashlib.md5()
    for filename in files:
        with open(filename) as file:
            m.update(file.read())
    _src_digest = m.digest()
    return _src_digest

_src_digest = None
