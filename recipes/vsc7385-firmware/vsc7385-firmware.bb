SECTION = "firmware"
DESCRIPTION = "VSC7385 Ethernet switch firmware"

PR = "r0"

SRC_URI = "file://vsc2bin"
FILES_${PN} = "/"

do_install () {
	install ${WORKDIR}/vsc2bin ${D}/
}
