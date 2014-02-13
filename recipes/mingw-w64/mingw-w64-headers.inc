require mingw-w64.inc

DESCRIPTION += "This is the windows headers."
SUMMARY = "MinGW-w64 (Windows) headers"

C_DEPENDS = "native:cc"
LIBTOOL_DEPENDS = ""

EXTRA_OECONF += "--without-crt"

PACKAGES = "${PN}"
FILES_${PN} = "${includedir}"
PROVIDES_${PN} += "gcc-bootstrap-libc-headers"
