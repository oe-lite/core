# inherit this for (single) library recipes

PROVIDES_${PN}		= "_${PF}"
PROVIDES_${PN}-dev	= "${PN} ${P} ${PF}"
DEPENDS_${PN}-dev	= "_${PF}"
