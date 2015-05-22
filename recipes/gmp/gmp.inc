SUMMARY = "The GNU Multiple Precision Arithmetic Library"
DESCRIPTION = "GMP is a free library for arbitrary precision arithmetic, \
	operating on signed integers, rational numbers, and \
	floating-point numbers."
HOMEPAGE = "https://gmplib.org/"

RECIPE_TYPES = "native machine sdk"

require conf/fetch/gnu.conf
SRC_URI = "${GNU_MIRROR}/gmp/gmp-${PV}.tar.xz"

DEPENDS = "native:m4 native:gawk libm"

inherit autotools c++ make-vpath

export CC_FOR_BUILD="${BUILD_CC}"
export CPP_FOR_BUILD="${BUILD_CPP}"

EXTRA_OECONF = '--enable-cxx --enable-fft --without-readline'

EXTRA_OECONF:>native = ' --disable-static'

#acpaths = ""

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "gmp gmpxx"
FILES_${PN}-libgmp-dev = "${includedir}/gmp.h"
FILES_${PN}-libgmpxx-dev = "${includedir}/gmpxx.h"
DEPENDS_${PN} = "libgmp libgmpxx"
DEPENDS_${PN}-dev = "libgmp-dev libgmpxx-dev"
RDEPENDS_${PN} = "libgmp libgmpxx"
RDEPENDS_${PN}-dev = "libgmp-dev libgmpxx-dev"
DEPENDS_${PN}-libgmpxx = "libgcc libm libc libstdc++ libgmp"

# Local Variables:
# mode: python
# End:
