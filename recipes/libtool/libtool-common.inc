# -*- mode:python; -*-
DESCRIPTION = "Generic library support script \
This is GNU libtool, a generic library support script.  Libtool hides \
the complexity of generating special library types (such as shared \
libraries) behind a consistent interface."
HOMEPAGE = "http://www.gnu.org/software/libtool/libtool.html"

RECIPE_TYPES = "machine native cross sdk-cross"

require conf/fetch/gnu.conf
SRC_URI = "${GNU_MIRROR}/libtool/libtool-${PV}.tar.gz"

inherit autotools

C_DEPENDS = "target-cross:cc"

LIBTOOL_DEPENDS = "host-cross:libtool"
LIBTOOL_DEPENDS:native = ""

EXTRA_OECONF_PROGRAM_PREFIX = "--program-prefix=${TARGET_PREFIX}"
EXTRA_OECONF_PROGRAM_PREFIX:machine = ""
EXTRA_OECONF += "${EXTRA_OECONF_PROGRAM_PREFIX}"

# When cross compiling libtool, we need to lie a bit, telling
# configure that host=target
HOST_ARCH:cross			= "${TARGET_ARCH}"
HOST_FPU:cross			= "${TARGET_FPU}"
HOST_EXEEXT:cross		= "${TARGET_EXEEXT}"
HOST_PREFIX:cross		= "${TARGET_PREFIX}"
HOST_CPPFLAGS:cross		= "${TARGET_CPPFLAGS}"
HOST_CFLAGS:cross		= "${TARGET_CFLAGS}"
HOST_LDFLAGS:cross		= "${TARGET_LDFLAGS}"
HOST_ARCH:sdk-cross		= "${TARGET_ARCH}"
HOST_FPU:sdk-cross		= "${TARGET_FPU}"
HOST_EXEEXT:sdk-cross		= "${TARGET_EXEEXT}"
HOST_PREFIX:sdk-cross		= "${TARGET_PREFIX}"
HOST_CPPFLAGS:sdk-cross		= "${TARGET_CPPFLAGS}"
HOST_CFLAGS:sdk-cross		= "${TARGET_CFLAGS}"
HOST_LDFLAGS:sdk-cross		= "${TARGET_LDFLAGS}"

do_install[postfuncs] += "do_install_symlinks"
do_install_symlinks () {
    ln -sf ../../aclocal ${D}${datadir}/libtool/libltdl/m4
    ln -sf ../config ${D}${datadir}/libtool/libltdl/config
}

PACKAGES = "${PN}-dbg ${PN}-doc ${PN}"

DEPENDS += "target:libgcc"

FILES_${PN}	= "\
${base_bindir}/* ${base_sbindir}/* \
${bindir}/* ${sbindir}/* \
${sysconfdir} ${sharedstatedir} ${localstatedir} \
${datadir}/${PN} ${datadir}/aclocal \
"

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "ltdl"
FILES_${PN}-libltdl-dev = "${includedir}/libltdl ${includedir}/ltdl.h"
PACKAGE_TYPE_${PN}-libltdl = "${TARGET_TYPE}"
PACKAGE_TYPE_${PN}-libltdl-dev = "${TARGET_TYPE}"
