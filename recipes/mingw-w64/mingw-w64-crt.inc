require mingw-w64.inc

DESCRIPTION += "This is the windows runtime."
SUMMARY = "MinGW-w64 (Windows) runtime"

C_DEPENDS_HOST = "host-cross:gcc-bootstrap"
LIBTOOL_DEPENDS = ""

DEPENDS += "mingw-w64-headers"

EXTRA_OECONF += "--without-headers"
EXTRA_OECONF += "--with-sysroot=${HOST_SYSROOT}${includedir}/.."

PACKAGES = "${PN} ${PN}-dev"
FILES_${PN} = ""
PROVIDES_${PN} = "libc libm"
DEPENDS_${PN} = "${PN}-dev_${PV} mingw-w64-headers"
DEPENDS_${PN}-dev = ""
