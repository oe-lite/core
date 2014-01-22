HOMEPAGE = "http://gcc.gnu.org/"

require conf/fetch/gnu.conf
SRC_URI = "${GNU_MIRROR}/gcc/gcc-${PV}/gcc-${PV}.tar.bz2"
S = "${SRCDIR}/gcc-${PV}"

FILESPATHPKG = "${P}:${PN}:gcc-${@'.'.join(d.get('PV').split('.')[:2])}"

inherit make make-vpath c c++

DEPENDS += "target-cross:binutils target:linux-headers"
DEPENDS += "host:mpc host:mpfr host:gmp host:isl host:cloog"
DEPENDS += "host:libz"

CC[export]	= ""
CPP[export]	= ""
CXX[export]	= ""
CXXCPP[export]	= ""
F77[export]	= ""
CXX[export]	= ""

CPPFLAGS[export]        = ""

BLACKLIST_VAR += "LD_LIBRARY_PATH"

GCC_PROGS = "gcc cpp"
BINUTIL_PROGS = "ar as ld nm ranlib strip objdump"

B_SYSROOT = "${B}/sysroot"
D_SYSROOT = "${D}${prefix}/${TARGET_ARCH}/sysroot"

do_configure[prefuncs] += "do_configure_sysroot"
do_configure_sysroot() {
	mkdir ${B_SYSROOT}
	for d in ${TARGET_SYSROOT}/* ; do
		cp -a $d ${B_SYSROOT}
	done
	mkdir -p ${B_SYSROOT}/bin
	for prog in ${BINUTIL_PROGS} ; do
		ln -sf `which ${TARGET_PREFIX}$prog` \
			${B_SYSROOT}/bin/$prog
		ln -sf `which ${HOST_PREFIX}$prog` \
			${B_SYSROOT}/bin/${HOST_ARCH}-$prog
	done
	for prog in ${GCC_PROGS} ; do
		ln -sf `which ${HOST_PREFIX}$prog` \
			${B_SYSROOT}/bin/${HOST_ARCH}-$prog
	done
}

# ARCH dependent configure options

ARCH_HAS_WITH_ARCH:TARGET_CPU_arm = "1"
ARCH_HAS_WITH_CPU:TARGET_CPU_arm = "1"
ARCH_HAS_WITH_TUNE:TARGET_CPU_arm = "1"
ARCH_HAS_WITH_ABI:TARGET_CPU_arm = "1"
ARCH_HAS_WITH_FPU:TARGET_CPU_arm = "1"

ARCH_HAS_WITH_ARCH:TARGET_CPU_x86 = "1"
ARCH_HAS_WITH_TUNE:TARGET_CPU_x86 = "1"

ARCH_HAS_WITH_ARCH:TARGET_CPU_m68k = "1"
ARCH_HAS_WITH_CPU:TARGET_CPU_m68k = "1"
ARCH_HAS_WITH_TUNE:TARGET_CPU_m68k = "1"
ARCH_HAS_WITH_FLOAT:TARGET_CPU_m68k = "1"

ARCH_HAS_WITH_CPU:TARGET_CPU_powerpc = "1"
ARCH_HAS_WITH_TUNE:TARGET_CPU_powerpc = "1"
ARCH_HAS_WITH_ABI:TARGET_CPU_powerpc = "1"
ARCH_HAS_WITH_FLOAT:TARGET_CPU_powerpc = "1"

do_configure_args ?= ""
addhook set_configure_arch to post_recipe_parse after arch_update
def set_configure_arch(d):
    args = []
    for arg_name in ('arch', 'cpu', 'tune'):
        if not d.get('ARCH_HAS_WITH_' + arg_name.upper()):
            continue
        arg_value = d.get('TARGET_M' + arg_name.upper())
        if not arg_value:
            continue
        args.append('--with-%s=%s'%(arg_name, arg_value))
    for arg_name in ('abi', 'fpu', 'float'):
        if not d.get('ARCH_HAS_WITH_' + arg_name.upper()):
            continue
        arg_value = d.get('TARGET_' + arg_name.upper())
        if not arg_value:
            continue
        args.append('--with-%s=%s'%(arg_name, arg_value))
    arg_value = d.get('TARGET_' + arg_name.upper())
    d.set('do_configure_args',
          ' '.join(filter(None, [d.get('do_configure_args')] + args)))

do_configure_gcc() {
	CPPFLAGS="${CPPFLAGS}" \
	${S}/configure \
	--build=${BUILD_ARCH} \
	--host=${HOST_ARCH} \
	--target=${TARGET_ARCH} \
	--program-prefix=${TARGET_PREFIX} \
	--prefix=${D}${prefix} \
	--bindir=${D}${bindir} \
	--sbindir=${D}${sbindir} \
	--libexecdir=${D}${libexecdir} \
	--sysconfdir=${D}${sysconfdir} \
	--sharedstatedir=${D}${sharedstatedir} \
	--localstatedir=${D}${localstatedir} \
	--libdir=${D}${libdir} \
	--includedir=${D}${includedir} \
	--datarootdir=${D}${datadir} \
	--infodir=${D}${infodir} \
	--mandir=${D}${mandir} \
	--with-sysroot=${D_SYSROOT} \
	--with-build-sysroot=${B_SYSROOT} \
	--with-local-prefix=${target_prefix}/local \
	--with-as=`which ${TARGET_AS}` \
	--with-ld=`which ${TARGET_LD}` \
	--with-native-system-header-dir=${target_includedir} \
	--enable-checking=release \
	--disable-nls \
	--disable-multilib \
	--disable-multiarch \
	--with-system-zlib \
	${do_configure_args} \
	$*
}

do_compile_targets = ""
do_compile() {
	oe_runmake ${do_compile_targets}
}

do_install_targets = "install"
do_install() {
	make ${do_install_targets}
	if [ -f "${D}${bindir}/${TARGET_PREFIX}c++" ]; then
		rm -f ${D}${bindir}/${TARGET_PREFIX}c++
		ln -s ${TARGET_PREFIX}g++ ${D}${bindir}/${TARGET_PREFIX}c++
	fi
	rm -f ${D}${bindir}/${TARGET_PREFIX}gcc-${PV}
	target_libdir=${D_SYSROOT}${target_libdir}
	target_libdir_parent=`dirname $target_libdir`
	for libdir in "${D}/${TARGET_ARCH}/lib"* ; do
		[ -e "$libdir" ] || continue
		mkdir -p $target_libdir_parent
		mv $libdir $target_libdir_parent/`basename $libdir`
	done
	for d in "${D}/share/gcc-${PV}/python/"* ; do
		[ -e "$d" ] || continue
		mkdir -p ${D_SYSROOT}${target_datadir}/gcc-${PV}/python
		mv $d ${D_SYSROOT}${target_datadir}/gcc-${PV}/python/
	done
	if [ -d "${D_SYSROOT}${target_libdir}" ]; then
		for lib in "${D}${libdir}/gcc/${TARGET_ARCH}/${PV}/lib"*.a ; do
			[ -e "$lib" ] || continue
			mv "$lib" "${D_SYSROOT}${target_libdir}/"
			ln -s ../../../../${TARGET_ARCH}/sysroot${target_libdir}/`basename $lib` $lib
		done
	fi
}

# Local Variables:
# mode: python
# End:
