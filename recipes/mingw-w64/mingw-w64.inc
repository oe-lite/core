DESCRIPTION = "Mingw-w64 delivers runtime, headers and libs for developing both 64 bit (x64) and 32 bit (x86) windows applications using GCC and other free software compilers."

RECIPE_TYPES = "machine sdk"

COMPATIBLE_HOST_ARCHS = ".*-mingw.*"

require conf/fetch/sourceforge.conf
SRC_URI = "${SOURCEFORGE_MIRROR}/mingw-w64/mingw-w64/mingw-w64-release/mingw-w64-v${PV}.tar.bz2"
S = "${SRCDIR}/mingw-w64-v${PV}"

inherit autotools make-vpath
