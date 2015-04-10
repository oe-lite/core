require mingw-w64.inc
S .= "/mingw-w64-libraries/winpthreads"

DESCRIPTION += "This is the windows pthreads library."
SUMMARY = "MinGW-w64 (Windows) pthreads library"

C_DEPENDS_HOST = "host-cross:gcc-bootstrap"
LIBTOOL_DEPENDS = ""

DEPENDS += "mingw-w64-crt"

EXTRA_OECONF += "--with-sysroot=${HOST_SYSROOT}${includedir}/.."

inherit library
PACKAGES = "${PN} ${PN}-dev"
PROVIDES_${PN} = "libpthread"

# Override dummy files (stubs) from gcc
FILE_PRIORITY_${PN}-dev = "1"
