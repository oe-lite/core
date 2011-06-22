# -*- mode:python; -*-
#
# inherit this for (single) library recipes
#

DEPENDS_${PN}		= "${PN}-dev_${PV}"
RDEPENDS_${PN}-dev	= "${PN}_${PV}"
