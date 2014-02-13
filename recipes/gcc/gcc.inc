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
	--with-gxx-include-dir=${D_SYSROOT}${target_includedir}/c++
}

do_compile_targets:canadian-cross = "all-gcc"

do_install_targets:canadian-cross = "install-gcc"

PROVIDES_${PN} = "cc"
PROVIDES_${PN}-g++ = "c++"

FILES_${PN}[qa] += "allow-libs-in-bindirs"
PROVIDES_${PN}[qa] += "allow-missing-provides:liblto-plugin"

inherit auto-package-utils
AUTO_PACKAGE_UTILS = "cpp g++ gcov"
FILES_${PN}-g++ = "${bindir}/${TARGET_PREFIX}c++"

PACKAGES += "${PN}-g++-dev"
FILES_${PN}-g++-dev = "/${TARGET_ARCH}/sysroot${target_includedir}/c++"

PACKAGE_TYPE_${PN}-g++-dev = "${TARGET_TYPE}"

DEPENDS_${PN}-g++ += "${PN} target:${PN}-g++-dev"
DEPENDS_${PN} += "${PN}-cpp"

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "gcc gcov asan tsan atomic gomp itm mudflap mudflapth ssp \
	stdc++ supc++ quadmath"
AUTO_PACKAGE_LIBS:canadian-cross = ""
AUTO_PACKAGE_LIBS_LIBDIR = "/${TARGET_ARCH}/sysroot${target_libdir}:lib:,_s,_eh,_nonshared,_pic"
#AUTO_PACKAGE_LIBS_DEV_FILES .= ",_eh.a,_nonshared.a,_nonshared.la,_pic.a,_pic.map,.spec,_preinit.o"
AUTO_PACKAGE_LIBS_DEV_FILES .= ",.map,.spec,_preinit.o"
AUTO_PACKAGE_LIBS_TYPE = "${TARGET_TYPE}"
PACKAGE_TYPE_${PN}-libgcc = "${TARGET_TYPE}"
PACKAGE_TYPE_${PN}-libgcc-dev = "${TARGET_TYPE}"
FILES_${PN}-libstdc++-dev = "/${TARGET_ARCH}/sysroot${target_datadir}/gcc-${PV}/python/libstdcxx"
PROVIDES_${PN}-libgcc = "libgcc-s"
PROVIDES_${PN}-libgcc[qa] = "allow-missing-soname:libgcc"
#DEPENDS_${PN}-libgcc = "libc"
RDEPENDS_${PN}-libgcc = "libc"
RDEPENDS_${PN}-libatomic = "libc libpthread"
RDEPENDS_${PN}-libgomp = "libc libpthread"
DEPENDS_${PN}-libitm = "libgcc"
RDEPENDS_${PN}-libitm = "libc libgcc libpthread"
RDEPENDS_${PN}-libmudflap = "libc libdl"
RDEPENDS_${PN}-libmudflapth = "ld-so libc libdl"
RDEPENDS_${PN}-libssp = "libc"
DEPENDS_${PN}-libstdc++ = "libgcc"
RDEPENDS_${PN}-libstdc++ = "ld-so libc libgcc libm"

# FIXME: remove the empty packages instead
PROVIDES_${PN}-libgcov[qa] = "allow-missing-soname"
PROVIDES_${PN}-libasan[qa] = "allow-missing-soname"
PROVIDES_${PN}-libtsan[qa] = "allow-missing-soname"
PROVIDES_${PN}-libsupc++[qa] = "allow-missing-soname"
PROVIDES_${PN}-libquadmath[qa] = "allow-missing-soname"

DEPENDS_${PN} += "binutils target:libgcc target:libc ${DEPENDS_HOSTLIB}"
DEPENDS_${PN}:>TARGET_BINFMT_elf = " target:ld-so"

META_EMIT_PREFIX += "split:PACKAGE_TYPE_${PN}"

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
    os.symlink('../../' + d.get('TARGET_TYPE'),
               os.path.join(pkg, target_arch, 'sysroot'))
    os.symlink('sysroot' + d.get('target_includedir'),
               os.path.join(pkg, target_arch, 'include'))
    os.symlink('sysroot' + d.get('target_libdir'),
               os.path.join(pkg, target_arch, 'lib'))

# Local Variables:
# mode: python
# End:
