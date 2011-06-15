# -*- mode:python; -*-
#
# inherit this for (single) library recipes
#

PROVIDES_${PN}		= "_${P}"
PROVIDES_${PN}-dev	= "${PN} ${P}"
DEPENDS_${PN}-dev	= "_${P}"
