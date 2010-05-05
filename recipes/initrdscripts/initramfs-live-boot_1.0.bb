DESCRIPTON = "A live image init script"

SRC_URI = "file://init-live.sh"

PR = "r6"

do_install() {
        install -m 0755 ${WORKDIR}/init-live.sh ${D}/init
        touch ${D}/servicemode
}

FILES_${PN} += "/init /servicemode"
