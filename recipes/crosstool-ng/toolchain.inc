# -*- mode:python; -*-

FILESPATHPKG = "${P}:${PN}:toolchain-${PV}:toolchain-${@'.'.join('${PV}'.split('.')[:2])}:toolchain:files"

# FIXME: come up with a more elegant solution. if not before, it then when
# fx. uclibc or eglibc is used, or even more, if llvm compiler is added
TOOLCHAIN_VERSION			= "gcc${CT_CC_VERSION}"
TOOLCHAIN_VERSION:>TARGET_OS_linux-gnu	= "-glibc${CT_LIBC_VERSION}"
TOOLCHAIN_VERSION:>TARGET_OS_linux-gnueabi	= "-glibc${CT_LIBC_VERSION}"
TOOLCHAIN_VERSION:>TARGET_OS_mingw32	= "-mingwrt${CT_MINGWRT_VERSION}"

# Depend on the right version of the ct-ng tool
DEPENDS := "native:crosstool-ng_${PV}"

PV .= "-${TOOLCHAIN_VERSION}"

S = "${WORKDIR}/build"
B = "${S}"

TUI_DEPENDS				= "host:libtermcap host:libreadline"
DEPENDS:>machine			= "${TUI_DEPENDS}"
DEPENDS:>sdk				= "${TUI_DEPENDS}"
DEPENDS:>canadian-cross			= "${TUI_DEPENDS}"

# FIXME: allow machine/sdk/canadian-cross toolchains to be built
# statically, to make it more robust against host machine differences

# FIXME: this looks REALLY wrong!
DEPENDS:>canadian-cross += "target:libdl target:libpthread target:libm"

# Let Crosstool NG manage compiler and linker flags etc.
AWK		= ""
STRIP		= "${D}/bin/${TARGET_PREFIX}strip"
CC		= ""
CPP		= ""
CXX		= ""
F77		= ""
OBJCOPY		= "${D}/bin/${TARGET_PREFIX}objcopy"
CXX		= ""
AR		= ""
NM		= ""
LD		= ""
CCLD		= ""
DLLTOOL		= ""
AS		= ""
OBJDUMP		= ""
AR		= ""
RANLIB		= ""
YACC		= ""
LEX		= ""

CFLAGS		= ""
CPPFLAGS	= ""
CXXFLAGS	= ""
LDFLAGS		= ""
LD_LIBRARY_PATH = ""

CONFIG_SITE	= ""

DEFCONFIG_CPU				= "defconfig.${TARGET_CPU}"
DEFCONFIG_CPU:TARGET_CPU_i386		= "defconfig.x86"
DEFCONFIG_CPU:TARGET_CPU_i486		= "defconfig.x86"
DEFCONFIG_CPU:TARGET_CPU_i586		= "defconfig.x86"
DEFCONFIG_CPU:TARGET_CPU_i686		= "defconfig.x86"
DEFCONFIG_CPU:TARGET_CPU_i786		= "defconfig.x86"

# FIXME: find a proper solution for this gnueabi mess
DEFCONFIG_OS				= "defconfig.${TARGET_OS}"
DEFCONFIG_OS:>TARGET_OS_linux-gnueabi	= "defconfig.linux-gnu"

SRC_URI = "file://defconfig.misc file://defconfig.toolchain file://${DEFCONFIG_CPU} file://${DEFCONFIG_OS}"

inherit c++
CXX_DEPENDS:native	= ""
CXX_DEPENDS:cross	= ""
CXX_DEPENDS:sdk-cross	= ""

# default crosstool-ng build configuration (to be overridden in
# site.conf or local.conf)
export CT_PARALLEL_JOBS	?= "1"
CT_LOAD			= "0"

_CT_KERNEL_VERSION	= "CT_KERNEL_V_"
_CT_BINUTILS_VERSION	= "CT_BINUTILS_V_"
_CT_CC_VERSION		= "CT_CC_V_"
_CT_LIBC_VERSION	= "CT_LIBC_V_"
_CT_LIBC_GLIBC_VERSION	= "CT_LIBC_GLIBC_V_"
_CT_GDB_VERSION		= "CT_GDB_V_"
_CT_GMP_VERSION		= "CT_GMP_V_"
_CT_MPFR_VERSION	= "CT_MPFR_V_"
_CT_PPL_VERSION		= "CT_PPL_V_"
_CT_CLOOG_VERSION	= "CT_CLOOG_V_"
_CT_MPC_VERSION		= "CT_MPC_V_"
_CT_LIBELF_VERSION	= "CT_LIBELF_V_"
_CT_W32API_VERSION	= "CT_W32API_V_"
_CT_MINGWRT_VERSION	= "CT_MINGWRT_V_"

CT_ARCH_ARCH		= "${TARGET_MARCH}"
CT_ARCH_CPU		= "${TARGET_MCPU}"
CT_ARCH_TUNE		= "${TARGET_MTUNE}"

# FIXME: add crosstool-ng and OE-lite support for x86 -mfpmath option

CT_KERNEL_VERSION		= "${MACHINE_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:native	= "${BUILD_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:sdk-cross	= "${SDK_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:sdk		= "${SDK_CT_KERNEL_VERSION}"

#FIXME: revisit _VERSION below in CT-NG 1.10!
#(CT_LIBC_GLIBC_MIN_KERNEL=eglibc, CT_LIBC_GLIBC_MIN_KERNEL_VERSION=glibc).
CT_LIBC_GLIBC_MIN_KERNEL_VERSION = "${MACHINE_CT_LIBC_GLIBC_MIN_KERNEL}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:native = "${BUILD_CT_LIBC_GLIBC_MIN_KERNEL}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:sdk-cross = "${SDK_CT_LIBC_GLIBC_MIN_KERNEL}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:sdk = "${SDK_CT_LIBC_GLIBC_MIN_KERNEL}"

DEPENDS += "${TOOLCHAIN_DEPENDS}"
TOOLCHAIN_DEPENDS = ""
addhook toolchain_default_depends_fixup to post_recipe_parse
def toolchain_default_depends_fixup(d):
    if (d.getVar("RECIPE_TYPE", True) == "cross" and
        d.getVar("MACHINE_CT_KERNEL_VERSION", True) == "custom"):
        d.setVar("TOOLCHAIN_DEPENDS", "linux-headers")

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "\
  gcc dl stdc++ supc++ resolv util crypt pthread thread_db bfd \
  m rt anl BrokenLocale nsl memusage pcprofile SegFault \
  nss_files nss_dns nss_compat nss_nis nss_nisplus nss_hesiod \
"
AUTO_PACKAGE_LIBS_PKGPREFIX = "sysroot-lib"
AUTO_PACKAGE_LIBS_LIBDIR = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}:lib::.so,.so.*,-*.so: \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}:lib:::.so,.a,_nonshared.a,.la \
"
TARGET_PACKAGES = "${LIBS_AUTO_PACKAGES}"

addtask mangle after do_patch before do_configure
do_mangle[dirs] = "${SRCDIR}"
do_mangle () {

	if [ "${CT_KERNEL_VERSION}" != "custom" ]; then
		ct_kernel_version=${_CT_KERNEL_VERSION}`echo ${CT_KERNEL_VERSION}|tr . _`=y
	else
		ct_kernel_version="# ${_CT_KERNEL_VERSION} is not set"
	fi
	ct_binutils_version=${_CT_BINUTILS_VERSION}`echo ${CT_BINUTILS_VERSION}|tr . _`=y
	ct_cc_version=${_CT_CC_VERSION}`echo ${CT_CC_VERSION}|tr . _`=y
	ct_libc_version=${_CT_LIBC_VERSION}`echo ${CT_LIBC_VERSION}|tr . _`=y
	ct_libc_glibc_version=${_CT_LIBC_GLIBC_VERSION}`echo ${CT_LIBC_VERSION}|tr . _`=y
	ct_gdb_version=${_CT_GDB_VERSION}`echo ${CT_GDB_VERSION}|tr . _`=y
	ct_gmp_version=${_CT_GMP_VERSION}`echo ${CT_GMP_VERSION}|tr . _`=y
	ct_mpfr_version=${_CT_MPFR_VERSION}`echo ${CT_MPFR_VERSION}|tr . _`=y
	ct_ppl_version=${_CT_PPL_VERSION}`echo ${CT_PPL_VERSION}|tr . _`=y
	ct_cloog_version=${_CT_CLOOG_VERSION}`echo ${CT_CLOOG_VERSION}|tr . _`=y
	ct_mpc_version=${_CT_MPC_VERSION}`echo ${CT_MPC_VERSION}|tr . _`=y
	ct_libelf_version=${_CT_LIBELF_VERSION}`echo ${CT_LIBELF_VERSION}|tr . _`=y
	ct_w32api_version=${_CT_W32API_VERSION}`echo ${CT_W32API_VERSION}|tr . _`=y
	ct_mingwrt_version=${_CT_MINGWRT_VERSION}`echo ${CT_MINGWRT_VERSION}|tr . _`=y
	export ct_kernel_version ct_binutils_version ct_cc_version ct_libc_version ct_gdb_version ct_gmp_version ct_mpfr_version ct_ppl_version ct_cloog_version ct_mpc_version ct_libelf_version ct_w32api_version ct_mingwrt_version


	cat defconfig.misc ${DEFCONFIG_CPU} defconfig.toolchain ${DEFCONFIG_OS} | \
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${INGREDIENTS}"%' \
	    -e 's%\(CT_PREFIX_DIR\)=.*%\1="${D}"%' \
	    -e "s%\(CT_PARALLEL_JOBS\)=.*%\1=$CT_PARALLEL_JOBS%" \
	    -e 's%\(CT_LOAD\)=.*%\1=${CT_LOAD}%' \
	    -e 's%\(CT_BUILD\)=.*%\1="${BUILD_ARCH}"%' \
	    -e 's%\(CT_BUILD_PREFIX\)=.*%\1="${BUILD_PREFIX}"%' \
	    -e 's%\(CT_BUILD_SUFFIX\)=.*%\1=""%' \
	    -e 's%\(CT_TARGET_VENDOR\)=.*%\1="${TARGET_VENDOR}"%' \
	    -e 's%\(CT_TARGET_PREFIX\)=.*%\1="${TARGET_PREFIX}"%' \
	    -e 's%\(CT_TARGET_CFLAGS\)=.*%\1="${TARGET_OPTIMIZATION}"%' \
	    -e 's%\(CT_ARCH_ARCH\)=.*%\1="${CT_ARCH_ARCH}"%' \
	    -e 's%\(CT_ARCH_CPU\)=.*%\1="${CT_ARCH_CPU}"%' \
	    -e 's%\(CT_ARCH_TUNE\)=.*%\1="${CT_ARCH_TUNE}"%' \
	    -e 's%.*\(CT_ARCH_FLOAT_HW\).*%\1=${@["n","y"]["${TARGET_FPU}"!="0"]}%' \
	    -e 's%.*\(CT_ARCH_FLOAT_SW\).*%\1=${@["y","n"]["${TARGET_FPU}"!="0"]}%' \
    	    -e "s%# __${_CT_KERNEL_VERSION}%$ct_kernel_version%" \
    	    -e "s%# __${_CT_BINUTILS_VERSION}%$ct_binutils_version%" \
    	    -e "s%# __${_CT_CC_VERSION}%$ct_cc_version%" \
    	    -e "s%# __${_CT_LIBC_VERSION}%$ct_libc_version\n$ct_libc_glibc_version%" \
            -e "s%\(CT_LIBC_GLIBC_MIN_KERNEL\)=.*%\1_VERSION=\"${CT_LIBC_GLIBC_MIN_KERNEL_VERSION}\"%" \
    	    -e "s%# __${_CT_GDB_VERSION}%$ct_gdb_version%" \
    	    -e "s%# __${_CT_GMP_VERSION}%$ct_gmp_version%" \
    	    -e "s%# __${_CT_MPFR_VERSION}%$ct_mpfr_version%" \
    	    -e "s%# __${_CT_PPL_VERSION}%$ct_ppl_version%" \
    	    -e "s%# __${_CT_CLOOG_VERSION}%$ct_cloog_version%" \
    	    -e "s%# __${_CT_MPC_VERSION}%$ct_mpc_version%" \
    	    -e "s%# __${_CT_LIBELF_VERSION}%$ct_libelf_version%" \
    	    -e "s%# __${_CT_W32API_VERSION}%$ct_w32api_version%" \
    	    -e "s%# __${_CT_MINGWRT_VERSION}%$ct_mingwrt_version%" \
    	> defconfig

    if [ CT_KERNEL_VERSION != CT_LIBC_GLIBC_MIN_KERNEL_VERSION ]; then
        mv defconfig defconfig.tmp
        cat defconfig.tmp |
           sed -e 's%CT_LIBC_GLIBC_KERNEL_VERSION_AS_HEADERS=y%CT_LIBC_GLIBC_KERNEL_VERSION_AS_HEADERS=n%' \
               -e 's%\# CT_LIBC_GLIBC_KERNEL_VERSION_CHOSEN is not set%CT_LIBC_GLIBC_KERNEL_VERSION_CHOSEN=y%' \
           > defconfig
    fi

	mv defconfig defconfig.tmp
	if [ "${CT_KERNEL_VERSION}" == "custom" ] ; then
		sed -e 's%.*\(CT_KERNEL_LINUX_USE_CUSTOM_HEADERS\).*%\1=y%' \
		    -e 's%.*\(CT_KERNEL_LINUX_CUSTOM_PATH\).*%\1="${TARGET_SYSROOT}${target_includedir}/.."%' \
		< defconfig.tmp > defconfig
	else
		sed -e 's%# \(CT_KERNEL_LINUX_INSTALL\) is not set%\1=y%' \
		    -e 's%# \($ct_kernel_version\) is not set%\1=y%' \
		< defconfig.tmp > defconfig
	fi		

	# FIXME: should we strip the -Wl, off TARGET_LDFLAGS ??
	#    -e 's%\(CT_TARGET_LDFLAGS\)=.*%\1="${TARGET_LDFLAGS}"%'

}

addtask fetch_tarballs after do_mangle before do_configure
do_fetch_tarballs[dirs] = "${B}"
do_fetch_tarballs () {
	sed -e 's%\(CT_SAVE_TARBALLS_DIR\)=.*%\1=n%' \
	    -e 's%\(CT_SAVE_TARBALLS\)=.*%\1=n%' \
	    -e 's%.*\(CT_ONLY_DOWNLOAD\).*%\1=y%' \
	    -e 's%.*\(CT_CROSS\).*%\1=y%' \
    	< ${SRCDIR}/defconfig > .config
	ct-ng oldconfig
	ct-ng build
}

addtask save_tarballs after do_fetch_tarballs before do_configure
do_save_tarballs[dirs] = "${B}"
python do_save_tarballs () {
	import dircache, os, shutil, bb
	urls = []
	for file in dircache.listdir("targets/tarballs"):
		srcfile = "%s/%s"%("targets/tarballs", file)
		dstfile = "%s/%s"%(bb.data.getVar("INGREDIENTS", d, 1), file)
		md5file = "%s.md5"%(dstfile)
		lckfile = "%s.lock"%(dstfile)
		if not os.path.islink(srcfile):
			lf = bb.utils.lockfile(lckfile)
			shutil.copyfile(srcfile, dstfile)
			md5data = bb.utils.md5_file(dstfile)
			md5out = open(md5file, "w")
			try:
				md5out.write(md5data)
			finally:
				md5out.close()
			bb.utils.unlockfile(lf)
}

DOT_CONFIG_MANGLING:machine = "\
	sed -e 's%.*\(CT_CANADIAN\).*%\1=y%' \
	    -e 's%\(CT_HOST\)=.*%\1=\"${HOST_ARCH}\"%' \
	    -e 's%\(CT_HOST_PREFIX\)=.*%\1=\"${HOST_PREFIX}\"%' \
	    -e 's%\(CT_HOST_SUFFIX\)=.*%\1=\"\"%' \
	    -e 's%\(CT_BINUTILS_EXTRA_CONFIG\)=.*%\1=\"--enable-targets=${TARGET_ARCH}\"%' \
	    -e 's%\(CT_BINUTILS_FOR_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_COMP_LIBS_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_DEBUG_gdb\)=.*%\1=n%' \
"

DOT_CONFIG_MANGLING:cross = "\
	sed -e 's%.*\(CT_CROSS\).*%\1=y%' \
	    -e 's%\(CT_GDB_CROSS\)=.*%\1=n%' \
"

DOT_CONFIG_MANGLING:sdk-cross = "\
	sed -e 's%.*\(CT_CROSS\).*%\1=y%' \
	    -e 's%\(CT_GDB_CROSS\)=.*%\1=n%' \
"

DOT_CONFIG_MANGLING:canadian-cross = "\
	sed -e 's%.*\(CT_CANADIAN\).*%\1=y%' \
	    -e 's%\(CT_HOST\)=.*%\1=\"${HOST_ARCH}\"%' \
	    -e 's%\(CT_HOST_PREFIX\)=.*%\1=\"${HOST_PREFIX}\"%' \
	    -e 's%\(CT_HOST_SUFFIX\)=.*%\1=\"\"%' \
	    -e 's%\(CT_BINUTILS_EXTRA_CONFIG\)=.*%\1=\"--enable-targets=${TARGET_ARCH}\"%' \
	    -e 's%\(CT_BINUTILS_FOR_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_COMP_LIBS_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_GDB_NATIVE\)=.*%\1=n%' \
	    -e 's%\(CT_GDB_GDBSERVER\)=.*%\1=n%' \
"

do_configure[dirs] = "${B}"
do_configure () {
	${DOT_CONFIG_MANGLING} <${SRCDIR}/defconfig > .config
	ct-ng oldconfig
}

addtask configure_qa after do_configure
do_configure_qa[dirs] = "${B}"
do_configure_qa () {
	fail=0

	if grep "CT_KERNEL_linux=y" .config >/dev/null; then

		if [ "${CT_KERNEL_VERSION}" != "custom" ]; then
			kernel_version=`grep CT_KERNEL_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
			if [ "$kernel_version" != "${CT_KERNEL_VERSION}" ]; then
				oewarn "CT_KERNEL_VERSION = $kernel_version (should be ${CT_KERNEL_VERSION})"
				fail=1
			else
				oenote "CT_KERNEL_VERSION = $kernel_version"
			fi
		fi

		libc_version=`grep CT_LIBC_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$libc_version" != "${CT_LIBC_VERSION}" ]; then
			oewarn "CT_LIBC_VERSION = $libc_version (should be ${CT_LIBC_VERSION})"
			fail=1
		else
			oenote "CT_LIBC_VERSION = $libc_version"
		fi

		gdb_version=`grep CT_GDB_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$gdb_version" != "${CT_GDB_VERSION}" ]; then
			oewarn "CT_GDB_VERSION = $gdb_version (should be ${CT_GDB_VERSION})"
			fail=1
		else
			oenote "CT_GDB_VERSION = $gdb_version"
		fi

	fi

	binutils_version=`grep CT_BINUTILS_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
	if [ "$binutils_version" != "${CT_BINUTILS_VERSION}" ]; then
		oewarn "CT_BINUTILS_VERSION = $binutils_version (should be ${CT_BINUTILS_VERSION})"
		fail=1
	else
		oenote "CT_BINUTILS_VERSION = $binutils_version"
	fi

	cc_version=`grep CT_CC_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
	if [ "$cc_version" != "${CT_CC_VERSION}" ]; then
		oewarn "CT_CC_VERSION = $cc_version (should be ${CT_CC_VERSION})"
		fail=1
	else
		oenote "CT_CC_VERSION = $cc_version"
	fi

	if grep "CT_GMP_NEEDED=y" .config >/dev/null; then
		gmp_version=`grep CT_GMP_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$gmp_version" != "${CT_GMP_VERSION}" ]; then
			oewarn "CT_GMP_VERSION = $gmp_version (should be ${CT_GMP_VERSION})"
			fail=1
		else
			oenote "CT_GMP_VERSION = $gmp_version"
		fi
	fi

	if grep "CT_MPFR_NEEDED=y" .config >/dev/null; then
		mpfr_version=`grep CT_MPFR_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$mpfr_version" != "${CT_MPFR_VERSION}" ]; then
			oewarn "CT_MPFR_VERSION = $mpfr_version (should be ${CT_MPFR_VERSION})"
			fail=1
		else
			oenote "CT_MPFR_VERSION = $mpfr_version"
		fi
	fi

	if grep "CT_PPL_NEEDED=y" .config >/dev/null; then
		ppl_version=`grep CT_PPL_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$ppl_version" != "${CT_PPL_VERSION}" ]; then
			oewarn "CT_PPL_VERSION = $ppl_version (should be ${CT_PPL_VERSION})"
			fail=1
		else
			oenote "CT_PPL_VERSION = $ppl_version"
		fi
	fi

	if grep "CT_CLOOG_NEEDED=y" .config >/dev/null; then
		cloog_version=`grep CT_CLOOG_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$cloog_version" != "${CT_CLOOG_VERSION}" ]; then
			oewarn "CT_CLOOG_VERSION = $cloog_version (should be ${CT_CLOOG_VERSION})"
			fail=1
		else
			oenote "CT_CLOOG_VERSION = $cloog_version"
		fi
	fi

	if grep "CT_MPC_NEEDED=y" .config >/dev/null; then
		mpc_version=`grep CT_MPC_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$mpc_version" != "${CT_MPC_VERSION}" ]; then
			oewarn "CT_MPC_VERSION = $mpc_version (should be ${CT_MPC_VERSION})"
			fail=1
		else
			oenote "CT_MPC_VERSION = $mpc_version"
		fi
	fi

	if grep "CT_LIBELF_NEEDED=y" .config >/dev/null; then
		libelf_version=`grep CT_LIBELF_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$libelf_version" != "${CT_LIBELF_VERSION}" ]; then
			oewarn "CT_LIBELF_VERSION = $libelf_version (should be ${CT_LIBELF_VERSION})"
			fail=1
		else
			oenote "CT_LIBELF_VERSION = $libelf_version"
		fi
	fi

	if grep "CT_KERNEL_mingw32=y" .config >/dev/null; then
		w32api_version=`grep CT_W32API_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$w32api_version" != "${CT_W32API_VERSION}" ]; then
			oewarn "CT_W32API_VERSION = $w32api_version (should be ${CT_W32API_VERSION})"
			fail=1
		else
			oenote "CT_W32API_VERSION = $w32api_version"
		fi
		mingwrt_version=`grep CT_MINGWRT_VERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$mingwrt_version" != "${CT_MINGWRT_VERSION}" ]; then
			oewarn "CT_MINGWRT_VERSION = $mingwrt_version (should be ${CT_MINGWRT_VERSION})"
			fail=1
		else
			oenote "CT_MINGWRT_VERSION = $mingwrt_version"
		fi
	fi

	if [ $fail != 0 ]; then
		oefatal "failed to configure the requested versions"
	fi
}

do_compile[dirs] = "${B}"
do_compile () {
	ct-ng build
}

# as do_compile actually installs into D, don't clean it on do_install
do_install[cleandirs] = ""
do_install[dirs] = "${D}"

# everything is already installed in do_compile, but let's rearrange it a bit
do_install () {
    mv ${TARGET_ARCH}/sys-root${target_base_libdir}/*.la \
       ${TARGET_ARCH}/sys-root${target_base_libdir}/*.a \
       ${TARGET_ARCH}/sys-root${target_libdir}/ || true
}

# We always build all packages, so care must be taken to choose the
# right sysroot packages as there can be multiple builds providing
# (almost) the same
PACKAGES = "${PN}-dbg ${PN}-g++ ${PN} ${PN}-doc ${PN}-locale ${PN}-gdb"

PROVIDES_${PN} = "cc"
DEPENDS_${PN} = "target:${PN}-sysroot-dev"
PROVIDES_${PN}-g++ = "c++"
DEPENDS_${PN}-g++ = "target:${PN}-sysroot-c++-dev"

DEPENDS_${PN}-sysroot-libnss-dns	= "${PN}-sysroot-libresolv"
RDEPENDS_${PN}-sysroot-libnss-dns	= "${PN}-sysroot-libresolv"
DEPENDS_${PN}-sysroot-librt-dev		= "${PN}-sysroot-libpthread-dev"
DEPENDS_${PN}-sysroot-librt		= "${PN}-sysroot-libpthread"
RDEPENDS_${PN}-sysroot-librt		= "${PN}-sysroot-libpthread"
DEPENDS_${PN}-sysroot-libstdc++-dev	= "${PN}-sysroot-libgcc-dev ${PN}-sysroot-libm-dev"
DEPENDS_${PN}-sysroot-libstdc++		= "${PN}-sysroot-libgcc ${PN}-sysroot-libm"
RDEPENDS_${PN}-sysroot-libstdc++	= "${PN}-sysroot-libgcc ${PN}-sysroot-libm"

# 1. The install/ dir maintains it's crosstool-ng layout, and all
# FILES_* variables must therefore use crosstool-ng layout paths.

# 2. A fixup function should then be used to move files around inside
# the packages directories to get proper cross and sysroot package
# paths.

FILES_${PN} = "\
${base_bindir} \
${base_libdir}/*.so.* \
${base_libdir}/gcc/${TARGET_ARCH} \
${base_libdir}/libiberty.a \
${base_libexecdir}/gcc/${TARGET_ARCH} \
${base_prefix}/${TARGET_ARCH}/bin \
${base_prefix}/${TARGET_ARCH}/lib \
${base_libdir}64 \
${base_prefix}/${TARGET_ARCH}/lib64 \
"

FILES_${PN}-c++ = "\
${base_bindir}/*++ \
${base_prefix}/${TARGET_ARCH}/bin/*++ \
"

FILES_${PN}-doc += "\
${base_prefix}/build.log* \
"

FILES_${PN}-dbg += "\
${base_prefix}/${TARGET_ARCH}/bin/.debug \
${libexecdir}/gcc/${TARGET_ARCH}/${GCC_VERSION}/.debug \
${libexecdir}/gcc/${TARGET_ARCH}/${GCC_VERSION}/*/.debug \
"

TARGET_PACKAGES += "${PN}-sysroot-libc"
FILES_${PN}-sysroot-libc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libc.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libc-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/ld.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/ld-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/ld-*.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}64 \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}64 \
"
DEPENDS_${PN}-sysroot-libc = "${PN}-sysroot-libc-dev_${PV}"
PROVIDES_${PN}-sysroot-libc = "libc"

TARGET_PACKAGES += "${PN}-sysroot-libc-dev"
# FIXME: the lib64 symlink should be in separate package!
FILES_${PN}-sysroot-libc-dev = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/libc.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/libc.a \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/libc_nonshared.a \
"
RDEPENDS_${PN}-sysroot-libc-dev = "${PN}-sysroot-libc_${PV}"
PROVIDES_${PN}-sysroot-libc-dev = "libc-dev"

TARGET_PACKAGES += "${PN}-sysroot-gdbserver-dbg"
FILES_${PN}-sysroot-gdbserver-dbg = "\
${base_prefix}/${TARGET_ARCH}/debug-root${target_bindir}/.debug \
"

TARGET_PACKAGES += "${PN}-sysroot-gdbserver"
FILES_${PN}-sysroot-gdbserver = "\
${base_prefix}/${TARGET_ARCH}/debug-root${target_bindir}/gdbserver \
${base_prefix}/${TARGET_ARCH}/debug-root${target_mandir}/man1/gdbserver.1 \
${datadir}/gdb \
"
RDEPENDS_${PN}-sysroot-gdbserver = "${PN}-sysroot-libdl"

TARGET_PACKAGES += "${PN}-sysroot-dbg"
FILES_${PN}-sysroot-dbg = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_bindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_bindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_sbindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_sbindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libexecdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libexecdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/gconv/.debug \
"

TARGET_PACKAGES += "${PN}-sysroot-c++-dev"
FILES_${PN}-sysroot-c++-dev = "${base_prefix}/${TARGET_ARCH}/include/c++"
DEPENDS_${PN}-sysroot-c++-dev  = "${PN}-sysroot-dev"
RDEPENDS_${PN}-sysroot-c++-dev = "${PN}-sysroot-dev"

TARGET_PACKAGES += "${PN}-sysroot-dev"
FILES_${PN}-sysroot-dev = "\
${base_prefix}/${TARGET_ARCH}/include \
${base_prefix}/${TARGET_ARCH}/sys-root${target_includedir} \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/*.a \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/*.o \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/*.py \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/*.la \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/ldscripts \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/*.o \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/*.a \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/*.la \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/gconv \
${base_prefix}/${TARGET_ARCH}/sys-root/mingw \
"
DEPENDS_${PN}-sysroot-dev  = "${PN}-sysroot-libc ${PN}-sysroot-libgcc"
RDEPENDS_${PN}-sysroot-dev = "${PN}-sysroot-libc-dev ${PN}-sysroot-libgcc-dev"

FILES_${PN}-sysroot-dev:>TARGET_OS_mingw32 = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_bindir}/*.dll \
"

TARGET_PACKAGES += "${PN}-sysroot-doc"
FILES_${PN}-sysroot-doc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_infodir} \
${base_prefix}/${TARGET_ARCH}/sys-root${target_mandir} \
${base_prefix}/${TARGET_ARCH}/sys-root${target_docdir} \
"

# Hackeydihack.... should instead get all sysroot doc in target_docdir
FILES_${PN}-sysroot-doc:>TARGET_OS_mingw32 = "\
${base_prefix}/${TARGET_ARCH}/sys-root/doc/runtime \
"

TARGET_PACKAGES += "${PN}-sysroot-locale"
FILES_${PN}-sysroot-locale = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_datadir}/locale \
${base_prefix}/${TARGET_ARCH}/sys-root${target_datadir}/i18n \
"

EXTRA_FILES_${PN}-sysroot-libgcc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libgcc_s.so.* \
"

EXTRA_FILES_${PN}-sysroot-libgcc-dev = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libgcc_s.so \
"

EXTRA_FILES_${PN}-sysroot-libm-dev = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/libieee.a \
"

EXTRA_FILES_${PN}-sysroot-libbfd = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/libbfd-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}/libbfd.so"

TARGET_PACKAGES += "${PN}-sysroot-nscd"
FILES_${PN}-sysroot-nscd = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_sbindir}/nscd"
PROVIDES_${PN}-sysroot-nscd = "target:util/rpcgen target:util/nscd"
PROVIDES_${PN}-sysroot-nscd:machine = ""
PROVIDES_${PN}-sysroot-nscd:sdk = ""
PROVIDES_${PN}-sysroot-nscd:canadian-cross = ""

TARGET_PACKAGES += "${PN}-sysroot-rpc"
FILES_${PN}-sysroot-rpc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_bindir}/rpcgen \
${base_prefix}/${TARGET_ARCH}/sys-root${target_sbindir}/rpcinfo \
${base_prefix}/${TARGET_ARCH}/sys-root${target_sysconfdir}/rpc"
PROVIDES_${PN}-sysroot-rpc = "target:util/rpcgen target:util/rpcinfo"
PROVIDES_${PN}-sysroot-rpc:machine = ""
PROVIDES_${PN}-sysroot-rpc:sdk = ""
PROVIDES_${PN}-sysroot-rpc:canadian-cross = ""

TARGET_PACKAGES += "${PN}-sysroot-ldconfig"
FILES_${PN}-sysroot-ldconfig = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_sbindir}/ldconfig"
PROVIDES_${PN}-sysroot-ldconfig = "target:util/ldconfig"
PROVIDES_${PN}-sysroot-ldconfig:machine = ""
PROVIDES_${PN}-sysroot-ldconfig:sdk = ""
PROVIDES_${PN}-sysroot-ldconfig:canadian-cross = ""

TARGET_PACKAGES += "${PN}-sysroot-ldd"
FILES_${PN}-sysroot-ldd = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_bindir}/ldd"
PROVIDES_${PN}-sysroot-ldd = "target:util/ldd"
PROVIDES_${PN}-sysroot-ldd:machine = ""
PROVIDES_${PN}-sysroot-ldd:sdk = ""
PROVIDES_${PN}-sysroot-ldd:canadian-cross = ""

TARGET_PACKAGES += "${PN}-sysroot-catchsegv"
FILES_${PN}-sysroot-catchsegv = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_bindir}/catchsegv"
PROVIDES_${PN}-sysroot-catchsegv = "target:util/catchsegv"
PROVIDES_${PN}-sysroot-catchsegv:machine = ""
PROVIDES_${PN}-sysroot-catchsegv:sdk = ""
PROVIDES_${PN}-sysroot-catchsegv:canadian-cross = ""

TARGET_PACKAGES += "${PN}-sysroot-sprof"
FILES_${PN}-sysroot-sprof = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_bindir}/sprof"
PROVIDES_${PN}-sysroot-sprof = "target:util/sprof"
PROVIDES_${PN}-sysroot-sprof:machine = ""
PROVIDES_${PN}-sysroot-sprof:sdk = ""
PROVIDES_${PN}-sysroot-sprof:canadian-cross = ""

TARGET_PACKAGES += "${PN}-sysroot-timezone-utils"
FILES_${PN}-sysroot-timezone-utils = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_bindir}/tzselect \
${base_prefix}/${TARGET_ARCH}/sys-root${target_sbindir}/zdump \
${base_prefix}/${TARGET_ARCH}/sys-root${target_sbindir}/zic \
${base_prefix}/${TARGET_ARCH}/sys-root${target_datadir}/zoneinfo \
"
PROVIDES_${PN}-sysroot-timezone-utils = "\
    target:util/tzselect target:util/zdump target:util/zic target:util/zoneinfo"
PROVIDES_${PN}-sysroot-timezone-utils:machine = ""
PROVIDES_${PN}-sysroot-timezone-utils:sdk = ""
PROVIDES_${PN}-sysroot-timezone-utils:canadian-cross = ""

TARGET_PACKAGES += "${PN}-sysroot-iconv-utils"
FILES_${PN}-sysroot-iconv-utils = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_bindir}/iconv \
${base_prefix}/${TARGET_ARCH}/sys-root${target_sbindir}/iconvconfig"
PROVIDES_${PN}-sysroot-iconv-utils = "target:util/iconv target:util/iconvconfig"
PROVIDES_${PN}-sysroot-iconv-utils:machine = ""
PROVIDES_${PN}-sysroot-iconv-utils:sdk = ""
PROVIDES_${PN}-sysroot-iconv-utils:canadian-cross = ""

# throw everything else in this garbage package, which is to be considered a WIP package aimed at being empty
TARGET_PACKAGES += "${PN}-sysroot-garbage"
FILES_${PN}-sysroot-garbage = "\
${base_prefix}/${TARGET_ARCH}/sys-root \
"

# Remaining / ignored files
#/include
#/lib (- /lib/gcc/${TARGET_ARCH})
#/${TARGET_ARCH}/debug-root


SPLIT_FUNCS += "split_sysroot_mangle"
SPLIT_FUNCS:>HOST_OS_mingw32 += " split_sysroot_mangle_mingw32"
SPLIT_FUNCS:>cross += " split_sysroot_mangle_stage"
SPLIT_FUNCS:>sdk-cross += " split_sysroot_mangle_stage"
SPLIT_FUNCS:>native += " split_sysroot_mangle_stage"
SPLIT_FUNCS:>machine += " split_sysroot_mangle_sdk"
SPLIT_FUNCS:>sdk += " split_sysroot_mangle_sdk"
SPLIT_FUNCS:>canadian-cross += " split_sysroot_mangle_sdk"

# Move the machine sysroot packages into proper target layout
split_sysroot_mangle () {
	cd ${PKGD}
	# Fixup the layout of the sysroot packages
	for pkg in ${TARGET_PACKAGES} ; do
		if [ -d $pkg/${TARGET_ARCH} ] ; then
			(
			cd $pkg/${TARGET_ARCH}
			if [ -d debug-root ] ; then
				mv debug-root/* ../
				rmdir debug-root
			fi
			if [ -d sys-root ] ; then
				mv sys-root/* ../
				rmdir sys-root
			fi
			if [ -L include ] ; then
				rm -f include
			fi
			if [ -d include ] ; then
				mkdir -p ../${target_includedir}
				cp -r include/* ../${target_includedir}
				rm -rf include
			fi
			rm -f lib
			if [ -d lib ] ; then
				mkdir -p ../${target_libdir}
				mv lib/* ../${target_libdir}
				rmdir lib
			fi
			cd ..
			rmdir ${TARGET_ARCH}
			)
		fi
	done
	ln -s ./sys-root/usr/include ${PN}/${TARGET_ARCH}/include
}

split_sysroot_mangle_mingw32 () {
    # Move object files (*.o) to usr/lib so that ld can find them through
    # the mingw/lib dir (mingw symlinks to /usr)
    for pkg in ${TARGET_PACKAGES} ; do
        if [ -d $pkg/lib ] ; then
            for f in $pkg/lib/*.o ; do
		test -f $f && mv $f $pkg${target_libdir}/
            done
	fi
    done
}

# Add symlinks to get sys-root back on stage for internal cross packages
split_sysroot_mangle_stage () {
	cd ${PKGD}
	ln -s ../../${TARGET_TYPE} ${PN}/${TARGET_ARCH}/sys-root
}

# Add empty sys-root dir in sdk packages
split_sysroot_mangle_sdk () {
	cd ${PKGD}
	mkdir -p ${PN}/${TARGET_ARCH}/sys-root
}

inherit libtool
LIBTOOL_DEPENDS = ""
LIBTOOL_FIXUP_SEARCH_DIRS += "\
${D}/${TARGET_ARCH}/sys-root${target_libdir} \
${D}/${TARGET_ARCH}/sys-root${target_base_libdir}"
LIBTOOL_FIXUP_STRIP_DIRS += "${D}/${TARGET_ARCH}/lib"

FIXUP_FUNCS =+ "toolchain_lafile_fixup"
toolchain_lafile_fixup () {
    for lafile in ${D}/${TARGET_ARCH}/sys-root${target_libdir}/*.la ; do
        sed -e "s:-L`readlink -f ${B}`/targets/${TARGET_ARCH}/[^ ']* *::" \
            -i $lafile
    done
}
