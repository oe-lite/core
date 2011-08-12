# -*- mode:python; -*-

DESCRIPTION ?= "Sanitized Linux kernel headers"
LICENSE ?= "GPL"

inherit kernel-common make

DEPENDS_KERNEL_HEADERS = "native:cc"
CLASS_DEPENDS += "${DEPENDS_KERNEL_HEADERS}"

do_configure() {
    oe_runmake allnoconfig
}
oe_runmake[emit] += "do_configure"

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
