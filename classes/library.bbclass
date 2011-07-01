# -*- mode:python; -*-
#
# inherit this for (single) library recipes
#

DEPENDS_${PN}		= "${PN}-dev_${PV}"
DEPENDS_${PN}-dev	= ""
RDEPENDS_${PN}-dev	= "${PN}_${PV}"
