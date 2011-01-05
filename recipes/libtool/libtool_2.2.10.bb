require libtool-2.2.inc

libtool_cross_compile = ""
libtool_cross_compile_recipe-cross = "file://cross_compile.patch"
libtool_cross_compile_recipe-sdk-cross = "file://cross_compile.patch"
SRC_URI_append += "${libtool_cross_compile}"

addtask bootstrap after do_patch before do_configure
do_bootstrap[dirs] = "${S}"

do_bootstrap () {
    ./bootstrap
}

do_bootstrap_recipe-native () {
    :
}
