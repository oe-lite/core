DESCRIPTION = "Arbitrary precision numeric processing language"

RECIPE_TYPES = "native sdk machine"

SRC_URI = "http://alpha.gnu.org/gnu/bc/bc-${PV}.tar.bz2"

inherit autotools

DEPENDS += "readline native:makeinfo"
EXTRA_OECONF += "--with-readline"
