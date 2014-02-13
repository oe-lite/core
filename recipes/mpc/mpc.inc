SUMMARY = "The GNU MPC Library"
DESCRIPTION = "C library for the arithmetic of complex numbers with \
	arbitrarily high precision and correct rounding of the result"
HOMEPAGE = "http://www.multiprecision.org"

RECIPE_TYPES = "native machine sdk"

SRC_URI = "http://www.multiprecision.org/mpc/download/mpc-${PV}.tar.gz"

DEPENDS = "native:sed native:grep native:gawk gmp mpfr"

inherit autotools c++ make-vpath library

EXTRA_OECONF = "--with-gmp=${HOST_SYSROOT} --with-mpfr=${HOST_SYSROOT}"
EXTRA_OECONF:>native = " --disable-static"
EXTRA_OECONF:>HOST_LIBC_mingw = " --enable-static --disable-shared"
