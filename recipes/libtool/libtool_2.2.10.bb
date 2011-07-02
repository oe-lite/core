require libtool-2.2.inc

libtool_cross_compile = ""
libtool_cross_compile:cross = "file://cross_compile.patch"
libtool_cross_compile:sdk-cross = "file://cross_compile.patch"
SRC_URI += "${libtool_cross_compile}"

addtask bootstrap after do_patch before do_configure
do_bootstrap[dirs] = "${S}"

do_bootstrap () {
	if [ "${RECIPE_TYPE}" != "native" ]; then
		./bootstrap
	fi
}
