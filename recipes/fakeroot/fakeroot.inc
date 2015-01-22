## Recipe for building fakeroot.
##
## From: http://man.he.net/man1/fakeroot:
## Fakeroot runs a command in an environment wherein it appears to have root
## privileges for file manipulation. Automatically added to the list of
## CLASS_DEPENDS by @class fakeroot.

DESCRIPTION = "Gives a fake root environment"
HOMEPAGE = "http://fakeroot.alioth.debian.org"

inherit autotools

RECIPE_TYPES="native"
DEPENDS = "native:libacl1-dev"

require conf/fetch/debian.conf
SRC_URI = "${DEBIAN_MIRROR}/main/f/fakeroot/fakeroot_${PV}.orig.tar.bz2"

SRC_URI += "file://configure-libtool.patch"

# fakeroot needs getopt which is provided by the util-linux package
DEPENDS_${PN} = "util-linux"
DEPENDS_${PN} = "${PN}-dev"
DEPENDS_${PN}-dev = ""
RDEPENDS_${PN} = "util-linux"

SOLIBS = "-*.so"
SOLIBSDEV = ".so"
FILES_${PN}-dev = "${libdir}/*.a ${libdir}/*.la \
	${sharedlibdir}/libfakeroot${SOLIBSDEV}"

# Local Variables:
# mode: python
# End:
