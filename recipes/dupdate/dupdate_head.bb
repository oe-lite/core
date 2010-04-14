DESCRIPTION = "Update daemon watching a dir for Deif updates."
LICENSE = "GPLv2"
SECTION = "console/utils"
DEPENDS = "mtd-utils"
RDEPENDS = "mtd-utils"

# upgrade: change SRCREV and bump PR
PR = "r5"

SRCREV = "58cb0ca1e9c310a372c08dc5d421e3a07782c058"
SRC_URI = "git://dev.doredevelopment.dk/srv/deif/git/dupdate.git;protocol=ssh"

S = "${WORKDIR}/git"

INITSCRIPT_PACKAGES = "${PN}"
INITSCRIPT_NAME_${PN} = "${PN}.sh"
INITSCRIPT_PARAMS_${PN} = "start 60 S ."
inherit update-rc.d

do_stage() {
	install -d ${STAGING_BINDIR}
	install -m 0755 ${S}/run_update.sh ${STAGING_BINDIR}/
	install -m 0755 ${S}/format_nand.sh ${STAGING_BINDIR}/
}

do_install() {
	install -d ${D}/${sbindir}
	install -p -m 755 ${S}/dupdate ${D}/${sbindir}
	install -p -m 755 ${S}/dboot ${D}/${sbindir}
	install -d ${D}/${sysconfdir}/init.d/
	install -p -m 755 ${S}/dupdate.sh ${D}/${sysconfdir}/init.d/

	install -m 0755 ${S}/reboot_to_servicemode ${D}/${sbindir}
}
