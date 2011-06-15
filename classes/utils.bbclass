# Various utility functions

# For compatibility
def uniq(iterable):
    import oe.utils
    return oe.utils.uniq(iterable)

def base_path_join(a, *p):
    return oe.path.join(a, *p)

def base_path_relative(src, dest):
    return oe.path.relative(src, dest)

def base_path_out(path, d):
    return oe.path.format_display(path, d)

def base_read_file(filename):
    return oe.utils.read_file(filename)

def base_ifelse(condition, iftrue = True, iffalse = False):
    return oe.utils.ifelse(condition, iftrue, iffalse)

def base_conditional(variable, checkvalue, truevalue, falsevalue, d):
    return oe.utils.conditional(variable, checkvalue, truevalue, falsevalue, d)

def base_less_or_equal(variable, checkvalue, truevalue, falsevalue, d):
    return oe.utils.less_or_equal(variable, checkvalue, truevalue, falsevalue, d)

def base_version_less_or_equal(variable, checkvalue, truevalue, falsevalue, d):
    return oe.utils.version_less_or_equal(variable, checkvalue, truevalue, falsevalue, d)

def base_contains(variable, checkvalues, truevalue, falsevalue, d):
    return oe.utils.contains(variable, checkvalues, truevalue, falsevalue, d)

def base_both_contain(variable1, variable2, checkvalue, d):
    return oe.utils.both_contain(variable1, variable2, checkvalue, d)

def base_prune_suffix(var, suffixes, d):
    return oe.utils.prune_suffix(var, suffixes, d)

def oe_filter(f, str, d):
    return oe.utils.str_filter(f, str, d)

def oe_filter_out(f, str, d):
    return oe.utils.str_filter_out(f, str, d)

def base_set_filespath(path, d):
    filespath = []
    # The ":" ensures we have an 'empty' override
    overrides = (bb.data.getVar("OVERRIDES", d, 1) or "") + ":"
    for p in path:
        for o in overrides.split(":"):
            filespath.append(os.path.join(p, o))
    return ":".join(filespath)

def oe_filter(f, str, d):
    from re import match
    return " ".join(filter(lambda x: match(f, x, 0), str.split()))

def oe_filter_out(f, str, d):
    from re import match
    return " ".join(filter(lambda x: not match(f, x, 0), str.split()))

oe_libinstall() {
    oefatal "oe_libinstall has been removed, as it was not proper in OE-lite.  Needs to figure out if it should be backported from OE-core and fixed, or if we can do something much simpler instead."
    oe_libinstall_not_implemented
}