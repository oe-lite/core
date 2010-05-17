SECTION = "console/utils"
DESCRIPTION = "Utility to generate bit patterns on address and data lines of memory various memory devices"
LICENSE = "GPLv2"
PR = "r0"

DEFAULT_PREFERENCE = "-1"

SRC_URI = "git://dev.doredevelopment.dk/mempattern.git;tag=${PV}"
S = "${WORKDIR}/git"

do_compile () {
	echo '${CC} ${CFLAGS} -DPOSIX -c' > conf-cc
	echo '${CC} ${LDFLAGS}' > conf-ld
	oe_runmake
}

do_install () {
	install -d ${D}${bindir}
	install -m 0755 mempattern ${D}${bindir}/
}
