SUMMARY = "Embedded GLIBC"
DESCRIPTION = "Embedded GLIBC (EGLIBC) is a variant of the GNU C Library \
	(GLIBC) that is designed to work well on embedded systems. EGLIBC \
	strives to be source and binary compatible with GLIBC. EGLIBC's goals \
	include reduced footprint, configurable components, better support for \
	cross-compilation and cross-testing."
HOMEPAGE = "http://www.eglibc.org/"

RECIPE_TYPES = "machine sdk"

COMPATIBLE_HOST_ARCHS = ".*-linux-gnu.* .*linux-uclibc.*"

SRC_BRANCH = "eglibc-${@d.get('PV').replace('.','_')}"
SRC_URI = "svn://www.eglibc.org/svn/branches/${SRC_BRANCH};protocol=http;rev=${SRC_REV}"
S = "${SRCDIR}/${SRC_BRANCH}/libc"

inherit autotools make-vpath

#do_unpack_fixup() {
#	#mv eglibc-${CT_LIBC_VERSION} eglibc-${CT_LIBC_VERSION}.tmp
#	mv ${SRC_BRANCH}/libc eglibc-${PV}
#	mv ${SRC_BRANCH}/* eglibc-${PV}
#}

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

do_configure[prefuncs] += "do_configure_siteinfo"
do_configure_siteinfo() {
	echo "libc_cv_ssp=no" > config.cache
}

EXTRA_OECONF += "\
	--disable-profile \
	--with-tls \
	--with-headers=${HOST_SYSROOT}${includedir} \
	--enable-kernel=${MIN_KERNEL_VERSION} \
	--with-__thread \
	--cache-file=config.cache \
"

#ld-linux do NOT support RPATH. See get-dynamic-info.h within the eglibc src
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
AUTO_PACKAGE_LIBS_DEPENDS = "ld-so libc"
AUTO_PACKAGE_LIBS_RDEPENDS = "ld-so libc"
FILES_${PN}-libthread-db += "${base_sharedlibdir}/libthread_db-*.so"

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
    d.set('DEPENDS_eglibc-libc', '${PN}-libc-dev_${PV} ld-so')
    d.set('RDEPENDS_eglibc-libc', 'ld-so')
    d.set('RDEPENDS_eglibc-libc-dev', '${PN}-libc_${PV}')

PACKAGES =+ "${PN}-libmcheck-dev"
FILES_${PN}-libmcheck-dev = "${libdir}/libmcheck.a"
PROVIDES_${PN}-libmcheck-dev = "libmcheck"

PACKAGES =+ "${PN}-libbsd-compat-dev"
FILES_${PN}-libmcheck-dev = "${libdir}/libbsd-compat.a"
PROVIDES_${PN}-libmcheck-dev = "libbsd-compat"

#FIXME: force libc on all lib package (R)DEPENDS and then override R(DEPENDS)
#for libc to remove it there

#addhook eglibc_pkgdepends to post_recipe_parse before auto_package_libs
#
#def eglibc_pkgdepends(d):
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

# FIXME: find a better way to package up the iconv .so modules.  Are they
# needed by some of the library calls?  Also, perhaps split it into different
# packages to allow selection of individual modules.  Do we need a
# gconv-modules file generated?  Perhaps create an image .oeclass for keeping
# selected modules and generate the gconv-modules file?
PACKAGES =+ "${PN}-gconv-modules"
FILES_${PN}-gconv-modules = "${libdir}/gconv"
PROVIDES_${PN}-gconv-modules = "gconv-modules"
DEPENDS_${PN}-gconv-modules = "libc"
RDEPENDS_${PN}-gconv-modules = "libc"
FILES_${PN}-gconv-modules[qa] += "allow-elf-bins-in-other-dirs"
FILES_${PN}-gconv-modules[qa] += "allow-elf-libs-in-other-dirs"
PROVIDES_${PN}-gconv-modules[qa] += "allow-missing-provides"
DEPENDS_${PN}-gconv-modules[qa] += "allow-missing-lib-depends"
RDEPENDS_${PN}-gconv-modules[qa] += "allow-missing-lib-rdepends"

RDEPENDS_${PN}-util-iconv += "gconv-modules"

CHRPATH_DIRS += "${libdir}/gconv"

FILES_${PN}-dev += "${libdir}/*.o ${libdir}/*/*.o"

DEPENDS_${PN}-dev = "linux-headers"

# Local Variables:
# mode: python
# End:
