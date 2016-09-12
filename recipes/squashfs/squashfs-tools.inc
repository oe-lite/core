DESCRIPTION = "Tool for creating and unpacking Squashfs filesystems"

RECIPE_TYPES = "native"

inherit c make

require conf/fetch/sourceforge.conf
SRC_URI = "${SOURCEFORGE_MIRROR}/squashfs/squashfs${PV}.tar.gz"
S = "${SRCDIR}/squashfs${PV}/squashfs-tools"

DEPENDS = "libz"

do_configure() {
	sed -e 's%^\(INSTALL_DIR\) *= .*%\1 = ${D}${bindir}%' \
	    -i Makefile
}

do_configure_enables = ""
do_configure[prefuncs] += "${do_configure_enables}"

RECIPE_FLAGS += "squashfs_tools_xz"
do_configure_xz() {
	sed -e 's/^#\?\(XZ_SUPPORT\) *= .*/\1 = 1/' \
	    -i Makefile
}
do_configure_enables:>USE_squashfs_tools_xz = " do_configure_xz"
DEPENDS:>USE_squashfs_tools_xz = " liblzma"

RECIPE_FLAGS += "squashfs_tools_lzo"
do_configure_lzo() {
	sed -e 's/^#\?\(LZO_SUPPORT\) *= .*/\1 = 1/' \
	    -i Makefile
}
do_configure_enables:>USE_squashfs_tools_lzo = " do_configure_lzo"
DEPENDS:>USE_squashfs_tools_lzo = " liblzo2"

RECIPE_FLAGS += "squashfs_tools_lz4"
do_configure_lz4() {
	sed -e 's/^#\?\(LZ4_SUPPORT\) *= .*/\1 = 1/' \
	    -i Makefile
}
do_configure_enables:>USE_squashfs_tools_lz4 = " do_configure_lz4"
DEPENDS:>USE_squashfs_tools_lz4 = " liblz4"

inherit auto-package-utils
AUTO_PACKAGE_UTILS = "mksquashfs unsquashfs"

DEPENDS_${PN} = "${AUTO_PACKAGE_UTILS_PROVIDES}"
RDEPENDS_${PN} = "${AUTO_PACKAGE_UTILS_PROVIDES}"

DEPENDS_${PN}-mksquashfs = "${DEPENDS}"
DEPENDS_${PN}-unsquashfs = "${DEPENDS}"
