NO_EXPANSION        = 0 # and False
FULL_EXPANSION      = 1 # and True
PARTIAL_EXPANSION   = 2
CLEAN_EXPANSION     = 3
OVERRIDES_EXPANSION = 4

from oelite.meta.meta import MetaData, ExpansionError
from oelite.meta.dict import DictMeta
from oelite.meta.cache import MetaCache

__all__ = [
    "NO_EXPANSION", "FULL_EXPANSION", "PARTIAL_EXPANSION", "CLEAN_EXPANSION",
    "OVERRIDES_EXPANSION",
    "MetaData", "ExpansionError",
    "DictMeta",
    "MetaCache", 
    ]


# Life-cycle for data objects:
#
# 1. Bakery parses oe-lite.conf with it's simpleparse.py,
#    creating a data object with it's simpledata.py
#    (but right now, we use confparse.py/ConfParser and
#     data/dict.py/DictMeta from meta/core)
# -> DONE
#
# 2. this data object (config) is passed to OEliteBaker.__init__
#    which creates a new oelite.meta.dict.DictMeta() object
# -> DONE
#
# 3. oelite.parse.ConfParser is used to parse oe-lite.conf, and
#    oelite.arch.init() modifies it, and base plus all ${INHERIT}'s is
#    parsed with OEParser, oelite.fetch.init() modifies it.
#    Both arch.init and fetch.init could perhaps be made into
#    standardized post_conf_parse hooks.
#
# 4. the new config/data object is copied for each recipe, and recipe
#    is parsed with OEParser.
#
# 5. for each value of ${RECIPE_TYPES}, the recipe data object copied
#    and the corresponding recipe type class is parsed
#
# 6. OEliteRecipe.__init__ calls all post_recipe_parse hooks on each
#    recipe data object.
#
# 7. this (dict based) data object is then "finalized", applying
#    overrides and append/prepend-overrides, and the result is stored
#    in a new SqliteData object, in a backend file in
#    TMPDIR/cache/data/recipe-name.sqlite . This file/database also
#    includes all information on files with mtime, so that next time
#    based on the recipe is only parsed if necessary.
#
# 8. the recipe is added to the runq database (:memory:), holding all
#    tasks and dependency information needed to decide what to build,
#    and in which order.
#
# 9. the task(s) to build, and all (recursive) dependencies are added
#    to runq.
#
# 10. all tasks to run are then hashed, datahash is calculated (or
#     read from database ie. file if present), and srchash (local file
#     parts of SRC_URI) is calculated, and finally dephash of all
#     dependencies (tasks) are calculated, and a metahash of all these
#     is calculated.
#
# 11. runq is processed, figuring out exactly which tasks needs to be
#     run.
#
# 12. tasks are run in order (allowing parallel tasks as much as
#     possible), and is executed with the dataobject (which is backed
#     by a persistent/cache file).  All existing variables are marked
#     as frozen, and changes to data variables or flags are saved in a
#     dict overlay, and discarded after task is run.  All expansions
#     are (still) cached in the dataobject, and is thus available for
#     reuse by other tasks of the same recipe, and for future calls
#     where data is reused from cache.
#
