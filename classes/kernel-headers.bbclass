# -*- mode:python; -*-

DESCRIPTION ?= "Sanitized Linux kernel headers"
LICENSE ?= "GPL"
require conf/kernel.conf

inherit kernel-common

do_configure() {
    oe_runmake allnoconfig
}

do_compile () {
    :
}

INSTALL_HDR_PATH ?= "${D}${includedir}/.."

do_install() {
    mkdir -p ${D}${includedir}
    oe_runmake INSTALL_HDR_PATH="${INSTALL_HDR_PATH}" headers_install
}

PACKAGES = "${PN}"
FILES_${PN} = "${includedir}"
PROVIDES_${PN} = "linux-headers"
