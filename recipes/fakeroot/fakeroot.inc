DESCRIPTION = "Gives a fake root environment"
HOMEPAGE = "http://fakeroot.alioth.debian.org"

inherit autotools

RECIPE_TYPES="native"

require conf/fetch/debian.conf
SRC_URI = "${DEBIAN_MIRROR}/main/f/fakeroot/fakeroot_${PV}.orig.tar.bz2"

SRC_URI += "file://configure-libtool.patch"

# fakeroot needs getopt which is provided by the util-linux package
DEPENDS_${PN} = "util-linux"
DEPENDS_${PN} = "${PN}-dev"
DEPENDS_${PN}-dev = ""
RDEPENDS_${PN} = "util-linux"
