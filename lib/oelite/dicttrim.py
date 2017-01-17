import sys

# Python's dicts never decreases their allocated capacity, even if one
# deletes most of their members. This means the dicts backing the
# DictMeta end up being quite oversized after we call filter_meta (in
# many cases, their fill factor is below 15%). The only way to get rid
# of that is to recreate the dict from scratch.
#
# Now, experimentation and reading CPython source code shows that
# d.copy() sizes the new dict so it has a fill factor between 25% and
# 50% - which means that it actually ends up using more memory if d
# had a fill factor between 50% and 66% (the latter usually being the
# maximum fill factor for any dict before Python resizes it), and
# doesn't do anything for fill factors between 25% and 50%, other than
# getting rid of dummy entries (those left behind from deletions).
#
# A better alternative is creating a temporary dict with
#
#   tmp = dict.fromkeys(d)
#
# This creates a dict with the same keys as d (literally same; they're
# "is"-identical in Python), with all values set to None. Then we do a
# trivial loop setting the value of each key appropriately. When
# replacing the value associated to an existing key, Python doesn't
# trigger resizing, so tmp ends up with the capacity from the
# fromkeys() call, which is closer to what we want.
#
# Now, Python before 2.7.10 contains a bug
# (https://bugs.python.org/issue23971) implying that fromkeys() sizes
# the dict so that its capacity is the smallest power-of-2 greater
# than the input length, so the final fill factor is somewhere in
# [0.5, 1.0) - thus violating the "fill factor usually less than
# 2/3". We don't care about a fill factor of 85%, but 99% may be
# noticable. If we'd hit that, we fall back to doing a d.copy() - for
# example, if the initial dict has a fill factor of 12%, the copy will
# end up with 48%, thus saving 75% of the memory used by the backing
# array, but avoiding the possible ill effects of a fill factor of
# 96%. This bug is fixed in Python 2.7.10+, where fromkeys() always
# returns a dict with a fill factor between 1/3 and 2/3.
#
# However, another bug present in all current 2.7.x releases
# (http://bugs.python.org/issue29019) means that fromkeys() also
# accounts for deleted entries in the passed-in dict when sizing, so
# we have to do a little extra dance to ensure we pass a dict without
# deleted entries.

if sys.version_info >= (2, 7, 10):
    def _use_dict_copy(d):
        return False
else:
    def _use_dict_copy(d):
        # If using the .fromkeys method, the final fill factor is between
        # 0.5 and 1.0, since the capacity is set to the smallest
        # power-of-2 greater than len(d).
        final_fill = float(len(d))
        while final_fill >= 1.0:
            final_fill /= 2.0
        # We want to avoid an almost completely full dict, but there's no
        # reason to set the bar as low as 2/3.
        return final_fill > 0.85

def trim(d):
    if len(d) == 0:
        tmp = {}
    elif _use_dict_copy(d):
        tmp = d.copy()
    else:
        tmp = dict.fromkeys(dict.fromkeys(d))
        for k,v in d.iteritems():
            tmp[k] = v
    # Ensure that we actually win something.
    delta = sys.getsizeof(d) - sys.getsizeof(tmp)
    if delta >= 0:
        # Use >= 0 rather than > 0 - even if we're only on par with
        # the original, the new one has no deleted entries, so lookups
        # in that one should be slightly faster.
        return tmp
    return d
