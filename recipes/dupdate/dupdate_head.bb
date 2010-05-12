DESCRIPTION = "Update daemon watching a dir for Deif updates."
LICENSE = "GPLv2"
SECTION = "console/utils"
DEPENDS = "mtd-utils"
RDEPENDS_${PN} = "mtd-utils"

# upgrade: change SRCREV and bump PR
PR = "r5"

SRCREV = "58cb0ca1e9c310a372c08dc5d421e3a07782c058"
SRC_URI = "git://dev.doredevelopment.dk/srv/deif/git/dupdate.git;protocol=ssh"

S = "${WORKDIR}/git"

PACKAGES += "${PN}-update ${PN}-format"
FILES_${PN}-update = "/run_update.sh"
FILES_${PN}-format = "/format_nand.sh"

do_install() {
	install -d ${D}/${sbindir} ${D}${sysconfdir}/rcS.d/
	install -p -m 755 ${S}/dupdate ${D}/${sbindir}
	install -p -m 755 ${S}/dboot ${D}/${sbindir}
	install -m 0755 ${S}/reboot_to_servicemode ${D}/${sbindir}

	install -d ${D}/${sysconfdir}/init.d/
	install -p -m 755 ${S}/dupdate.sh ${D}/${sysconfdir}/init.d/
	ln -s ../init.d/dupdate.sh ${D}${sysconfdir}/rcS.d/S60dupdate.sh

	# Not related to dupdate
	install -m 0755 ${S}/run_update.sh ${D}/
	install -m 0755 ${S}/format_nand.sh ${D}/
}
