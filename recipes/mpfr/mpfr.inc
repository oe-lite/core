SUMMARY = "The GNU MPFR Library"
DESCRIPTION = "C library for multiple-precision floating-point computations \
	with correct rounding"
HOMEPAGE = "http://www.mpfr.org"

RECIPE_TYPES = "native machine sdk"

SRC_URI = "http://www.mpfr.org/mpfr-current/mpfr-${PV}.tar.xz"

DEPENDS = "native:sed native:grep native:gawk gmp"

inherit autotools c++ make-vpath library

EXTRA_OECONF = "--with-gmp=${HOST_SYSROOT}"
EXTRA_OECONF:>native = " --disable-static"
