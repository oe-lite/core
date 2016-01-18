SRC_URI = "http://nixos.org/releases/${PN}/${P}/${P}.tar.bz2"
LICENSE = "GPLv3"
SUMMARY = "Tool to allow editing of RPATH and interpreter fields in ELF binaries"

inherit autotools c++ c

RECIPE_TYPES = "native sdk"

DEP = "host:libc host:libgcc host:libm host:libstdc++"
RDEPENDS_${PN} += "${DEP}"
DEPENDS_${PN} += "${DEP}"
EXTRA_OECONF += "CFLAGS=-static CXXFLAGS=-static"
