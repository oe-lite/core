SUMMARY = "Chunky Loop Generator"
DESCRIPTION = "CLooG is a free software and library to generate code for \
	scanning Z-polyhedra. That is, it finds a code (e.g. in C, FORTRAN...) \
	that reaches each integral point of one or more parameterized \
	polyhedra."
HOMEPAGE = "http://www.cloog.org/"

RECIPE_TYPES = "native machine sdk"

SRC_URI = "http://www.bastoul.net/cloog/pages/download/cloog-${PV}.tar.gz"

inherit autotools make-vpath library

LIBRARY_NAME = "libcloog-isl"

DEPENDS += "libgmp"
EXTRA_OECONF += "--with-gmp-prefix=${HOST_SYSROOT}"

DEPENDS += "libisl"
EXTRA_OECONF += "--with-isl-prefix=${HOST_SYSROOT}"

FILES_${PN}-dev += "${libdir}/*/*.cmake"

inherit auto-package-utils
AUTO_PACKAGE_UTILS = "cloog"
DEPENDS_${PN}-cloog = "libcloog-isl"
RDEPENDS_${PN}-cloog = "libcloog-isl"
