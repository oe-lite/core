DESCRIPTION = "Sanitized Linux kernel headers"
SECTION = "devel"
LICENSE = "GPL"

DEFAULT_DEPENDS = ""

inherit kernel-common

do_configure() {
    oe_runmake allnoconfig
}

do_compile () {
    :
}

INSTALL_HDR_PATH ?= "${D}${includedir}"

do_install() {
    oe_runmake INSTALL_HDR_PATH="${INSTALL_HDR_PATH}" \
        headers_install
}

PACKAGES = "${PN}"
FILES_${PN} = "${includedir}"
PROVIDES_${PN} = "linux-headers"
