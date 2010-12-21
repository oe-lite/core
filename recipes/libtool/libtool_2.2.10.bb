require libtool-2.2.inc

libtool_cross_compile = ""
libtool_cross_compile_recipe-cross = "file://cross_compile.patch;patch=1"
libtool_cross_compile_recipe-sdk-cross = "file://cross_compile.patch;patch=1"
SRC_URI_append += "${libtool_cross_compile}"

do_configure_prepend () {
    ./bootstrap
}
