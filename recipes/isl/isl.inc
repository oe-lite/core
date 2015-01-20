SUMMARY = "Integer Set Library"
DESCRIPTION = "Library for manipulating sets and relations of integer points \
	bounded by linear constraints."
HOMEPAGE = "http://isl.gforge.inria.fr/"

RECIPE_TYPES = "native machine sdk"

SRC_URI = "http://isl.gforge.inria.fr/isl-${PV}.tar.bz2"

inherit autotools c++ make-vpath library

DEPENDS = "libgmp"
EXTRA_OECONF += "--with-gmp-prefix=${HOST_SYSROOT}"
