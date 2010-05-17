SECTION = "console/utils"
DESCRIPTION = "Utility to generate bit patterns on address and data lines of memory various memory devices"
LICENSE = "GPLv2"

# to upgrade, change SRCREV and bump PR
PR = "r1"
SRCREV = "782b06faa027d4474ba33804ac0d7e670a5abb01"

SRC_URI = "git://git.doredevelopment.dk/mempattern.git;protocol=git"
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
