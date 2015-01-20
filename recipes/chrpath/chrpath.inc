RECIPE_TYPES = "native cross sdk-cross"

COMPATIBLE_TARGET_ARCHS = ".*linux .*darwin"

inherit autotools make-vpath

C_DEPENDS_HOST = "gcc-bootstrap"
C_DEPENDS_TARGET = ""

# Avoid circular dependencies
CHRPATH_DEPENDS:native = ""
CHRPATH_DEPENDS_TARGET = ""
CHRPATH_TYPES = "HOST"
CHRPATH_TYPES:native = ""
LIBTOOL_DEPENDS = "" # not actually using libtool anyway...

# We need to use a copy of chrpath to be able to modify the rpath of chrpath
# itself
TMP_BINDIR = "${D}/tmp-bindir"
DO_CHRPATH_NATIVE_PRE:native = "do_chrpath_native_pre"
do_chrpath[prefuncs] += "${DO_CHRPATH_NATIVE_PRE}"
def do_chrpath_native_pre(d):
    bindir = d.get("D") + d.get("bindir")
    tmpdir = d.get("TMP_BINDIR")
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    shutil.copy2(os.path.join(bindir, "chrpath"), tmpdir)
PATH:<native = "${TMP_BINDIR}:"
DO_CHRPATH_NATIVE_POST:native = "do_chrpath_native_post"
do_chrpath[postfuncs] += "${DO_CHRPATH_NATIVE_POST}"
def do_chrpath_native_post(d):
    tmpdir = d.get("TMP_BINDIR")
    shutil.rmtree(tmpdir)

# Local Variables:
# mode: python
# End:
