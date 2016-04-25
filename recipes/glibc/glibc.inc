SUMMARY = "The GNU C Library"
DESCRIPTION = """Any Unix-like operating system needs a C library:
the library which defines the ``system calls'' and other basic facilities such
as open, malloc, printf, exit...

The GNU C Library is used as the C library in the GNU systems and most systems
with the Linux kernel.
"""
HOMEPAGE = "http://www.gnu.org/software/libc/"

RECIPE_TYPES = "machine sdk"

COMPATIBLE_HOST_ARCHS = ".*-linux-gnu.* .*linux-uclibc.*"

SRC_URI = "git://sourceware.org/git/glibc.git;commit=${STABLE_COMMIT}"

S = "${SRCDIR}/glibc"

inherit autotools make-vpath

C_DEPENDS = "host-cross:gcc-bootstrap"

DEPENDS += "linux-headers"

LIBTOOL_DEPENDS = ""

MACHINE[unexport]       = "1"

RECIPE_FLAGS:native = "toolchain_kernel_version_native"
RECIPE_FLAGS:machine = "toolchain_kernel_version_machine"
RECIPE_FLAGS:sdk = "toolchain_kernel_version_sdk"

DEFAULT_USE_toolchain_kernel_version_native	= "2.6.32"
DEFAULT_USE_toolchain_kernel_version_machine	= "2.6.32"
DEFAULT_USE_toolchain_kernel_version_sdk	= "2.6.32"

MIN_KERNEL_VERSION = "${USE_toolchain_kernel_version_native}${USE_toolchain_kernel_version_machine}${USE_toolchain_kernel_version_sdk}"
MIN_KERNEL_VERSION[expand] = "3"

EXTRA_OECONF += "\
	--disable-profile \
	--with-tls \
	--with-headers=${HOST_SYSROOT}${includedir} \
	--enable-kernel=${MIN_KERNEL_VERSION} \
	--with-__thread \
	--cache-file=config.cache \
	libc_cv_slibdir='${base_libdir}' \
	libc_cv_localedir='${base_libdir}/locale' \
"

#ld-linux do NOT support RPATH. See get-dynamic-info.h within the glibc src
do_chrpath[postfuncs] += "do_chrpath_fix_ld"
do_chrpath_fix_ld[expand] = 3
do_chrpath_fix_ld () {
	${HOST_PREFIX}chrpath -d ${D}${base_libdir}/ld-${PV}.so
}

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "c m rt dl pthread thread_db util crypt anl nsl resolv \
	cidn nss_compat nss_db nss_dns nss_files nss_hesiod nss_nis \
	nss_nisplus memusage pcprofile BrokenLocale SegFault"
AUTO_PACKAGE_LIBS_LIBDIR = "${base_sharedlibdir}:lib:,-${PV}:.so,.so.*:"
AUTO_PACKAGE_LIBS_LIBDIR += "${sharedlibdir}:lib:::.so"
AUTO_PACKAGE_LIBS_LIBDIR += "${libdir}:lib:::.a,_nonshared.a,_pic.a,_pic.map"
AUTO_PACKAGE_LIBS:>HOST_CPU_powerpc = " nldbl"
AUTO_PACKAGE_LIBS_DEV_FILES .= ",_nonshared.a,_pic.a,_pic.map"
AUTO_PACKAGE_LIBS_DEV_DEPENDS = "${PN}-dev"
AUTO_PACKAGE_LIBS_DEV_RDEPENDS = "${PN}-dev"
AUTO_PACKAGE_LIBS_DEPENDS = "ld-so libc"
AUTO_PACKAGE_LIBS_RDEPENDS = "ld-so libc"
FILES_${PN}-libthread-db += "${base_sharedlibdir}/libthread_db-*.so"
PROVIDES_${PN}-libnldbl[qa] += "allow-missing-soname:libnldbl"

DEPENDS_${PN}-librt = "libpthread"
RDEPENDS_${PN}-librt = "libpthread"
DEPENDS_${PN}-libanl = "libpthread"
RDEPENDS_${PN}-libanl = "libpthread"
DEPENDS_${PN}-libnss-compat = "libnsl"
RDEPENDS_${PN}-libnss-compat = "libnsl"
DEPENDS_${PN}-libnss-db = "libnss-files"
RDEPENDS_${PN}-libnss-db = "libnss-files"
DEPENDS_${PN}-libnss-dns = "libresolv"
RDEPENDS_${PN}-libnss-dns = "libresolv"
DEPENDS_${PN}-libnss-hesiod = "libnss-files libresolv"
RDEPENDS_${PN}-libnss-hesiod = "libnss-files libresolv"
DEPENDS_${PN}-libnss-nis = "libnsl libnss-files"
RDEPENDS_${PN}-libnss-nis = "libnsl libnss-files"
DEPENDS_${PN}-libnss-nisplus = "libnsl"
RDEPENDS_${PN}-libnss-nisplus = "libnsl"
DEPENDS_${PN}-libmemusage = "libdl"
RDEPENDS_${PN}-libmemusage = "libdl"

addhook fixup_libc_pkgdepends to post_recipe_parse after auto_package_libs
def fixup_libc_pkgdepends(d):
    d.set('DEPENDS_glibc-libc', '${PN}-libc-dev_${PV} ld-so')
    d.set('RDEPENDS_glibc-libc', 'ld-so')
    d.set('RDEPENDS_glibc-libc-dev', '${PN}-libc_${PV}')

PACKAGES =+ "${PN}-libmcheck-dev"
FILES_${PN}-libmcheck-dev = "${libdir}/libmcheck.a"
PROVIDES_${PN}-libmcheck-dev = "libmcheck"

PACKAGES =+ "${PN}-libbsd-compat-dev"
FILES_${PN}-libmcheck-dev = "${libdir}/libbsd-compat.a"
PROVIDES_${PN}-libmcheck-dev = "libbsd-compat"

#FIXME: force libc on all lib package (R)DEPENDS and then override R(DEPENDS)
#for libc to remove it there

#addhook glibc_pkgdepends to post_recipe_parse before auto_package_libs
#
#def glibc_pkgdepends(d):
#    for lib in d.get('AUTO_PACKAGE_LIBS').split():
#        pkg = 'lib' + lib

PACKAGES += "${PN}-ld"
PROVIDES_${PN}-ld = "ld-so"
PROVIDES_${PN}-ld[qa] = "is-library"
FILES_${PN}-ld = "${base_sharedlibdir}/ld-${PV}.so ${base_sharedlibdir}/ld*.so.*"
PACKAGES =+ "${PN}-ld-dbg"
PROVIDES_${PN}-ld-dbg = "ld-so-dbg"
FILES_${PN}-ld-dbg = "${base_sharedlibdir}/.debug/ld-${PV}.so"

#Create a dummy package to satisfy ld-so-dev depends to work around
#that auto-package-libs copies all RDEPENDS_{PN}+"-dev" in as RDEPENDS
#for libs. ld-so is not a normal lib in that sence.
PACKAGES =+ "ld-so-dev"

inherit auto-package-utils
AUTO_PACKAGE_UTILS = "catchsegv gencat getconf getent iconv ldd locale \
	localedef makedb mtrace pcpfofiledump pldd rpcgen sotruss sprof \
	tzselect xtrace ldconfig sln pcprofiledump iconvconfig nscd zdump zic"
AUTO_PACKAGE_UTILS_BASENAME = "${PN}-util"
FILES_${PN}-util-locale += "${datadir}/i18n/locales ${datadir}/i18n/charmaps/"
FILES_${PN}-util-sotruss = "${sharedlibdir}/audit/sotruss-lib.so"
FILES_${PN}-dbg += "${sharedlibdir}/audit/.debug"
AUTO_PACKAGE_UTILS_RDEPENDS = "libc"
AUTO_PACKAGE_UTILS_DEPENDS = "libc"
DEPENDS_${PN}-util-nscd += "libnsl libpthread"
RDEPENDS_${PN}-util-nscd += "libnsl libpthread"
DEPENDS_${PN}-util-sprof += "libdl"
RDEPENDS_${PN}-util-sprof += "libdl"

require glibc-gconv-modules.inc

FILES_${PN}-dev += "${libdir}/*.o ${libdir}/*/*.o"

DEPENDS_${PN}-dev = "linux-headers"
RDEPENDS_${PN}-dev = "linux-headers"

# Local Variables:
# mode: python
# End:
