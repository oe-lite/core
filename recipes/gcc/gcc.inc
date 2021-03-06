SUMMARY = "GNU Compiler Collection"
DESCRIPTION = "The GNU Compiler Collection includes front ends for C, C++, \
	Objective-C, Fortran, Java, Ada, and Go, as well as libraries for \
	these languages (libstdc++, libgcj,...)."
HOMEPAGE = "http://gcc.gnu.org/"

FILESPATHPKG = "${P}:${PN}"

require gcc-common.inc

RECIPE_TYPES = "cross sdk-cross canadian-cross"

# Use gcc-bootstrap as target-compiler
C_DEPENDS_TARGET = "target-cross:gcc-bootstrap"
CXX_DEPENDS_TARGET = ""

DEPENDS += "${DEPENDS_LIBC}"
DEPENDS_LIBC = "target:libc target:libm target:libpthread"
DEPENDS_LIBC:>TARGET_BINFMT_elf = " target:ld-so target:libdl"

do_configure() {
	do_configure_gcc \
	--enable-languages=c,c++ \
	--enable-shared \
	--enable-__cxa_atexit \
	--enable-c99 \
	--enable-long-long \
	--enable-threads=posix \
	--enable-libstdcxx-time \
	--disable-libstdcxx-pch \
	--with-gxx-include-dir=${D_SYSROOT}${target_includedir}/c++ \
	--with-glibc-version="${USE_glibc_min_version}"
}

inherit libtool
LIBTOOL_DEPENDS = ""
LIBTOOL_FIXUP_SEARCH_DIRS_CROSS += "${D}${libexecdir}/gcc/${TARGET_ARCH}/${PV}"
LIBTOOL_FIXUP_STRIP_DIRS += "${HOST_SYSROOT} ${STAGE_DIR}/${TARGET_CROSS}"
LIBTOOL_FIXUP_STRIP_DIRS =+ "${D_SYSROOT}"
do_compile_targets:canadian-cross = "all-gcc"

do_install_targets:canadian-cross = "install-gcc"

PROVIDES_${PN} = "cc"
PROVIDES_${PN}-g++ = "c++"

FILES_${PN}[qa] += "allow-libs-in-bindirs"
PROVIDES_${PN}[qa] += "allow-missing-provides:liblto-plugin"

# Get rid of gcc-dev package
PACKAGES = "${PN}-dbg ${PN}-doc ${PN}-locale ${PN}"
FILES_${PN} += "${libdir}/*.a"

inherit auto-package-utils
AUTO_PACKAGE_UTILS = "cpp g++ gcov"
FILES_${PN}-g++ = "${bindir}/${TARGET_PREFIX}c++${HOST_EXEEXT}"

PACKAGES += "${PN}-g++-dev"
FILES_${PN}-g++-dev = "/${TARGET_ARCH}/sysroot${target_includedir}/c++${HOST_EXEEXT}"

PACKAGE_TYPE_${PN}-g++-dev = "${TARGET_TYPE}"

DEPENDS_${PN}-g++ += "${PN} target:${PN}-g++-dev"
RDEPENDS_${PN}-g++ += "${PN} target:${PN}-g++-dev"
DEPENDS_${PN} += "${PN}-cpp"
DEPENDS_${PN}:>TARGET_LIBC_mingw = " target:libpthread"
RDEPENDS_${PN}:>HOST_LIBC_mingw = " host:libpthread"

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "gcc gcov atomic gomp itm mudflap mudflapth ssp \
	stdc++ supc++ quadmath asan tsan ubsan lsan"
AUTO_PACKAGE_LIBS:canadian-cross = ""
AUTO_PACKAGE_LIBS_LIBDIR = "/${TARGET_ARCH}/sysroot${target_libdir}:lib:,_s,_s_sjlj,_eh,_nonshared,_pic,_nonshm"
AUTO_PACKAGE_LIBS_LIBDIR:>TARGET_LIBC_mingw = ":-*.dll /${TARGET_ARCH}/sysroot${target_sharedlibdir}:lib:,_s,_s_sjlj,_eh,_nonshared,_pic,_nonshm:-*.dll"
AUTO_PACKAGE_LIBS_DEV_FILES .= ",.map,.spec,_preinit.o"
AUTO_PACKAGE_LIBS_DEV_FILES:>TARGET_LIBC_mingw = ",.dll.a"
AUTO_PACKAGE_LIBS_TYPE = "${TARGET_TYPE}"
PACKAGE_TYPE_${PN}-libgcc = "${TARGET_TYPE}"
PACKAGE_TYPE_${PN}-libgcc-dev = "${TARGET_TYPE}"
# Let GCC crt* files have priority over those coming from libc
# (ie. mingw-w64-crt)
FILE_PRIORITY_${PN}-libgcc-dev = "1"
FILES_${PN}-libgcc-dev += "/${TARGET_ARCH}/sysroot${target_libdir}/crt*.o"
FILES_${PN}-libstdc++-dev = "/${TARGET_ARCH}/sysroot${target_datadir}/gcc-${PV}/python/libstdcxx /${TARGET_ARCH}/sysroot${target_libdir}/libstdc++*.py /${TARGET_ARCH}/sysroot${target_libdir}/libstdc++fs.la /${TARGET_ARCH}/sysroot${target_libdir}/libstdc++fs.a"
PROVIDES_${PN}-libgcc = "libgcc-s"
PROVIDES_${PN}-libgcc[qa] = "allow-missing-soname:libgcc"
#DEPENDS_${PN}-libgcc = "libc"
RDEPENDS_${PN}-libgcc = "libc"
RDEPENDS_${PN}-libatomic = "libc libpthread"
RDEPENDS_${PN}-libgomp = "libc libpthread"
DEPENDS_${PN}-libitm = "libgcc"
RDEPENDS_${PN}-libitm = "libc libgcc libpthread"
RDEPENDS_${PN}-libmudflap = "libc"
RDEPENDS_${PN}-libmudflap:>TARGET_BINFMT_elf = " libdl"
RDEPENDS_${PN}-libmudflapth = "libc"
RDEPENDS_${PN}-libmudflapth:>TARGET_BINFMT_elf = " ld-so libdl"
RDEPENDS_${PN}-libssp = "libc"
DEPENDS_${PN}-libstdc++ = "libc libgcc libm"
RDEPENDS_${PN}-libstdc++ = "libc libgcc libm"
RDEPENDS_${PN}-libstdc++:>TARGET_BINFMT_elf = " ld-so"

PACKAGES += "${PN}-libsanitizer-dev"
PACKAGE_TYPE_${PN}-libsanitizer-dev = "${TARGET_TYPE}"
FILES_${PN}-libsanitizer-dev = "/${TARGET_ARCH}/sysroot${target_libdir}/libsanitizer.spec"
DEPENDS_${PN}-libasan-dev += "${PN}-libsanitizer-dev"
DEPENDS_${PN}-libtsan-dev += "${PN}-libsanitizer-dev"
DEPENDS_${PN}-libubsan-dev += "${PN}-libsanitizer-dev"
DEPENDS_${PN}-liblsan-dev += "${PN}-libsanitizer-dev"
RDEPENDS_${PN}-libasan-dev += "${PN}-libsanitizer-dev"
RDEPENDS_${PN}-libtsan-dev += "${PN}-libsanitizer-dev"
RDEPENDS_${PN}-libubsan-dev += "${PN}-libsanitizer-dev"
RDEPENDS_${PN}-liblsan-dev += "${PN}-libsanitizer-dev"

# FIXME: remove the empty packages instead
PROVIDES_${PN}-libgcov[qa] = "allow-missing-soname"
PROVIDES_${PN}-libasan[qa] = "allow-missing-soname"
PROVIDES_${PN}-libtsan[qa] = "allow-missing-soname"
PROVIDES_${PN}-libsupc++[qa] = "allow-missing-soname"
PROVIDES_${PN}-libquadmath[qa] = "allow-missing-soname"

DEPENDS_${PN} += "binutils target:libgcc target:libc ${DEPENDS_HOSTLIB}"
RDEPENDS_${PN} += "binutils target:libgcc target:libc-dev ${DEPENDS_HOSTLIB}"
DEPENDS_${PN}:>TARGET_BINFMT_elf = " target:ld-so"

META_EMIT_PREFIX += "split:PACKAGE_TYPE_${PN}"

do_install[postfuncs] += "do_install_fixup_crt_files"
do_install_fixup_crt_files() {
	for f in ${D}${libdir}/gcc/${TARGET_ARCH}/${PV}/crt*.o ; do
		[ -f $f ] || continue
		mv $f ${D_SYSROOT}${target_libdir}/
	done
}

do_split[postfuncs] += 'do_split_sysroot_fixup'
def do_split_sysroot_fixup(d):
    target_type = d.get('TARGET_TYPE')
    target_arch = d.get('TARGET_ARCH')
    os.chdir(d.get('PKGD'))
    assert target_type
    for pkg in d.get('PACKAGES').split():
        pkg_type = d.get('PACKAGE_TYPE_' + pkg)
        if pkg_type != target_type:
            continue
        pkg_files = os.listdir(pkg)
        if not pkg_files:
            continue
        if pkg_files != [target_arch]:
            bb.fatal('target package with non-sysroot files: %s'%(pkg))
        pkg_files = os.listdir(os.path.join(pkg, target_arch))
        if not pkg_files:
            continue
        if pkg_files != ['sysroot']:
            bb.fatal('target package with non-sysroot files: %s'%(pkg))
        os.rename(os.path.join(pkg, target_arch, 'sysroot'), pkg + '.sysroot')
        os.rmdir(os.path.join(pkg, target_arch))
        os.rmdir(pkg)
        os.rename(pkg + '.sysroot', pkg)
    pkg = d.get('PN')
    os.mkdir(os.path.join(pkg, target_arch))
    if d.get('HOST_TYPE') == 'native':
        os.symlink('../../' + d.get('TARGET_TYPE'),
                   os.path.join(pkg, target_arch, 'sysroot'))
    else:
        os.mkdir(os.path.join(pkg, target_arch, 'sysroot'))

# Local Variables:
# mode: python
# End:
