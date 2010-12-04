FILESPATHPKG = "${PF}:${P}:${PN}:${BP}:${BPN}:toolchain-${PV}:toolchain:files"

# FIXME: come up with a more elegant solution. if not before, it then when
# fx. uclibc or eglibc is used, or even more, if llvm compiler is added
TOOLCHAIN_VERSION			= "gcc-${CT_CC_VERSION}"
TOOLCHAIN_VERSION_append_linux-gnu	= "-glibc-${CT_LIBC_VERSION}"
TOOLCHAIN_VERSION_append_linux-gnueabi	= "-glibc-${CT_LIBC_VERSION}"
TOOLCHAIN_VERSION_append_mingw32	= "-mingwrt-${CT_MINGWRT_VERSION}"

PR = "${TOOLCHAIN_VERSION}-"

# Depend on the right version of the ct-ng tool
DEPENDS = "crosstool-ng-native-${TOOLCHAIN_VERSION}"

S = "${WORKDIR}/build"
B = "${S}"

DEFAULT_DEPENDS_recipe-native		= ""
DEFAULT_DEPENDS_recipe-cross		= ""
DEFAULT_DEPENDS_recipe-sdk-cross	= ""

DEPENDS += "${TUI_DEPENDS}"
TUI_DEPENDS				= "ncurses-dev readline-dev"
TUI_DEPENDS_recipe-native		= ""
TUI_DEPENDS_recipe-cross		= ""
TUI_DEPENDS_recipe-sdk-cross		= ""
TUI_DEPENDS_recipe-sdk			= "ncurses-sdk-dev readline-sdk-dev"
TUI_DEPENDS_recipe-canadian-cross	= "ncurses-sdk-dev readline-sdk-dev"

# FIXME: this looks REALLY wrong!
DEPENDS_append_recipe-canadian-cross += "\
${TARGET_ARCH}/sysroot-libdl \
${TARGET_ARCH}/sysroot-libpthread \
${TARGET_ARCH}/sysroot-libm \
"

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

DEFCONFIG_CPU		= "defconfig.${TARGET_CPU}"
DEFCONFIG_CPU_i386	= "defconfig.x86"
DEFCONFIG_CPU_i486	= "defconfig.x86"
DEFCONFIG_CPU_i586	= "defconfig.x86"
DEFCONFIG_CPU_i686	= "defconfig.x86"
DEFCONFIG_CPU_i786	= "defconfig.x86"

# FIXME: find a proper solution for this gnueabi mess
DEFCONFIG_OS		= "defconfig.${TARGET_OS}"
DEFCONFIG_OS_linux-gnueabi= "defconfig.linux-gnu"

SRC_URI = "file://defconfig.misc file://defconfig.toolchain file://${DEFCONFIG_CPU} file://${DEFCONFIG_OS}"

inherit c++
DEFAULT_CXX_DEPENDS_recipe-native	= ""
DEFAULT_CXX_DEPENDS_recipe-cross	= ""
DEFAULT_CXX_DEPENDS_recipe-sdk-cross	= ""

# default crosstool-ng build configuration (to be overridden in
# site.conf or local.conf)
CT_PARALLEL_JOBS	?= "1"
CT_LOAD			= "0"

_CT_KERNEL_VERSION	= "CT_KERNEL_V_"
_CT_BINUTILS_VERSION	= "CT_BINUTILS_V_"
_CT_CC_VERSION		= "CT_CC_V_"
_CT_LIBC_VERSION	= "CT_LIBC_V_"
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

CT_KERNEL_VERSION	?= "custom"
CT_KERNEL_VERSION_CROSS	?= "${CT_KERNEL_VERSION}"
CT_KERNEL_VERSION_recipe-sdk-cross	= "${CT_KERNEL_VERSION_CROSS}"
CT_KERNEL_VERSION_recipe-sdk		= "${CT_KERNEL_VERSION_CROSS}"

DEPENDS += "${TOOLCHAIN_DEFAULT_DEPENDS}"
TOOLCHAIN_DEFAULT_DEPENDS = ""
python () {
	import bb
	kernel_version = bb.data.getVar("CT_KERNEL_VERSION", d, True)
	if kernel_version == "custom":
		bb.data.setVar("TOOLCHAIN_DEFAULT_DEPENDS", "linux-headers", d)
}

addtask mangle after do_patch before do_configure
do_mangle[dirs] = "${WORKDIR}"
do_mangle () {

	if [ "${CT_KERNEL_VERSION}" != "custom" ]; then
		ct_kernel_version=${_CT_KERNEL_VERSION}`echo ${CT_KERNEL_VERSION}|tr . _`=y
	else
		ct_kernel_version="# ${_CT_KERNEL_VERSION} is not set"
	fi
	ct_binutils_version=${_CT_BINUTILS_VERSION}`echo ${CT_BINUTILS_VERSION}|tr . _`=y
	ct_cc_version=${_CT_CC_VERSION}`echo ${CT_CC_VERSION}|tr . _`=y
	ct_libc_version=${_CT_LIBC_VERSION}`echo ${CT_LIBC_VERSION}|tr . _`=y
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
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${DL_DIR}"%' \
	    -e 's%\(CT_PREFIX_DIR\)=.*%\1="${D}"%' \
	    -e 's%\(CT_PARALLEL_JOBS\)=.*%\1=${CT_PARALLEL_JOBS}%' \
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
	    -e 's%.*\(CT_ARCH_FLOAT_HW\).*%\1=${@['n','y']["${TARGET_FPU}"!="0"]}%' \
	    -e 's%.*\(CT_ARCH_FLOAT_SW\).*%\1=${@['y','n']["${TARGET_FPU}"!="0"]}%' \
    	    -e "s%# __${_CT_KERNEL_VERSION}%$ct_kernel_version%" \
    	    -e "s%# __${_CT_BINUTILS_VERSION}%$ct_binutils_version%" \
    	    -e "s%# __${_CT_CC_VERSION}%$ct_cc_version%" \
    	    -e "s%# __${_CT_LIBC_VERSION}%$ct_libc_version%" \
    	    -e "s%\(CT_LIBC_GLIBC_MIN_KERNEL\)=.*%\1="${CT_LIBC_GLIBC_MIN_KERNEL}"%" \
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

	mv defconfig defconfig.tmp
	if [ x${CT_KERNEL_VERSION} == xcustom ] ; then
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
    	< ${WORKDIR}/defconfig > .config
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
		dstfile = "%s/%s"%(bb.data.getVar("DL_DIR", d, 1), file)
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

DOT_CONFIG_MANGLING = "\
	sed -e 's%.*\(CT_CANADIAN\).*%\1=y%' \
	    -e 's%\(CT_HOST\)=.*%\1="${HOST_ARCH}"%' \
	    -e 's%\(CT_HOST_PREFIX\)=.*%\1="${HOST_PREFIX}"%' \
	    -e 's%\(CT_HOST_SUFFIX\)=.*%\1=""%' \
	    -e 's%\(CT_BINUTILS_EXTRA_CONFIG\)=.*%\1="--enable-targets=${TARGET_ARCH}"%' \
	    -e 's%\(CT_BINUTILS_FOR_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_COMP_LIBS_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_DEBUG_gdb\)=.*%\1=n%' \
"

DOT_CONFIG_MANGLING_recipe-cross = "\
	sed -e 's%.*\(CT_CROSS\).*%\1=y%' \
	    -e 's%\(CT_GDB_CROSS\)=.*%\1=n%' \
"

DOT_CONFIG_MANGLING_recipe-sdk-cross = "\
	sed -e 's%.*\(CT_CROSS\).*%\1=y%' \
	    -e 's%\(CT_GDB_CROSS\)=.*%\1=n%' \
"

DOT_CONFIG_MANGLING_recipe-canadian-cross = "\
	sed -e 's%.*\(CT_CANADIAN\).*%\1=y%' \
	    -e 's%\(CT_HOST\)=.*%\1="${HOST_ARCH}"%' \
	    -e 's%\(CT_HOST_PREFIX\)=.*%\1="${HOST_PREFIX}"%' \
	    -e 's%\(CT_HOST_SUFFIX\)=.*%\1=""%' \
	    -e 's%\(CT_BINUTILS_EXTRA_CONFIG\)=.*%\1="--enable-targets=${TARGET_ARCH}"%' \
	    -e 's%\(CT_BINUTILS_FOR_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_COMP_LIBS_TARGET\)=.*%\1=n%' \
	    -e 's%\(CT_GDB_NATIVE\)=.*%\1=n%' \
	    -e 's%\(CT_GDB_GDBSERVER\)=.*%\1=n%' \
"

do_configure[dirs] = "${B}"
do_configure () {
	${DOT_CONFIG_MANGLING} <${WORKDIR}/defconfig > .config
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

# Stub out do_install
do_install () {
	:
}
do_install_recipe-cross () {
	:
}
do_install_recipe-sdk-cross () {
	:
}
do_install_recipe-canadian-cross () {
	:
}
# And as do_compile actually installs into D, don't clean it on do_install
do_install[cleandirs] = ""

# We always build all packages, so care must be taken to choose the
# right sysroot packages as there can be multiple builds providing
# (almost) the same
PACKAGES = "${PN}-dbg ${PN} ${PN}-doc ${PN}-locale ${PN}-gdb"

SYSROOT_PACKAGES = "\
	${PN}-sysroot-gdbserver \
	${PN}-sysroot-gdbserver-dbg \
	${PN}-sysroot-dbg \
	${PN}-sysroot-dev \
	${PN}-sysroot-doc \
	${PN}-sysroot-locale \
	${PN}-sysroot-libc \
	${PN}-sysroot-libdl \
	${PN}-sysroot-libnss-files \
	${PN}-sysroot-libnss-dns \
	${PN}-sysroot-libresolv \
	${PN}-sysroot-libutil \
	${PN}-sysroot-libcrypt \
	${PN}-sysroot-libpthread \
	${PN}-sysroot-libm \
	${PN}-sysroot-librt \
	${PN}-sysroot-libstdc++ \
	${PN}-sysroot-libgcc \
	${PN}-sysroot-garbage \
"

PROVIDES_${PN} += "toolchain${RE}"
PROVIDES_${PN}_append_recipe-cross	+= "${TARGET_ARCH}/toolchain"
PROVIDES_${PN}_append_recipe-sdk-cross	+= "${TARGET_ARCH}/toolchain"

DEPENDS_${PN}-sysroot-dev		= "${PN}-sysroot-libc ${PN}-sysroot-libgcc"
RDEPENDS_${PN}-sysroot-dev		= "${PN}-sysroot-libc ${PN}-sysroot-libgcc"

DEPENDS_${PN}-sysroot-libnss-dns	= "${PN}-sysroot-libresolv"
RDEPENDS_${PN}-sysroot-libnss-dns	= "${PN}-sysroot-libresolv"
DEPENDS_${PN}-sysroot-librt		= "${PN}-sysroot-libpthread"
RDEPENDS_${PN}-sysroot-librt		= "${PN}-sysroot-libpthread"
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

FILES_${PN}-doc += "\
${base_prefix}/build.log* \
"

FILES_${PN}-dbg += "\
${base_prefix}/${TARGET_ARCH}/bin/.debug \
${libexecdir}/gcc/${TARGET_ARCH}/${GCC_VERSION}/.debug \
${libexecdir}/gcc/${TARGET_ARCH}/${GCC_VERSION}/*/.debug \
"

FILES_${PN}-sysroot-gdbserver-dbg = "\
${base_prefix}/${TARGET_ARCH}/debug-root${target_bindir}/.debug \
"

FILES_${PN}-sysroot-gdbserver = "\
${base_prefix}/${TARGET_ARCH}/debug-root${target_bindir}/gdbserver \
${base_prefix}/${TARGET_ARCH}/debug-root${target_mandir}/man1/gdbserver.1 \
${datadir}/gdb \
"
RDEPENDS_${PN}-sysroot-gdbserver = "${PN}-sysroot-libdl"

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
"

FILES_${PN}-sysroot-dev_append_mingw32 = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_bindir}/*.dll \
"

FILES_${PN}-sysroot-doc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_infodir} \
${base_prefix}/${TARGET_ARCH}/sys-root${target_mandir} \
${base_prefix}/${TARGET_ARCH}/sys-root${target_docdir} \
"

# Hackeydihack.... should instead get all sysroot doc in target_docdir
FILES_${PN}-sysroot-doc_append_mingw32 = "\
${base_prefix}/${TARGET_ARCH}/sys-root/doc/runtime \
"

FILES_${PN}-sysroot-locale = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_datadir}/locale \
${base_prefix}/${TARGET_ARCH}/sys-root${target_datadir}/i18n \
"

# libc can depend on libnss_files libnss_dns
# dropbear libc libcrypt libutil
# ethercat libstdc++ libm libgcc_s
# performance-test-suite librt libm
# libnss_dns libresolv

FILES_${PN}-sysroot-libc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libc.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libc-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/ld.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/ld-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/ld-*.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}64 \
${base_prefix}/${TARGET_ARCH}/sys-root${target_libdir}64 \
"
# FIXME: the lib64 symlink should be in separate package!

FILES_${PN}-sysroot-libdl = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libdl.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libdl-*.so \
"

FILES_${PN}-sysroot-libcrypt = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libcrypt.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libcrypt-*.so \
"

FILES_${PN}-sysroot-libutil = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libutil-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libnss_dns-*.so \
"

FILES_${PN}-sysroot-libnss-files = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libnss_files-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libnss_files.so.* \
"

FILES_${PN}-sysroot-libnss-dns = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libnss_dns-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libnss_dns.so.* \
"

FILES_${PN}-sysroot-libresolv = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libresolv-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libresolv.so.* \
"

FILES_${PN}-sysroot-libpthread = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libpthread.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libpthread-*.so \
"

FILES_${PN}-sysroot-libm = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libm.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libm-*.so \
"

FILES_${PN}-sysroot-librt = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/librt.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/librt-*.so \
"

FILES_${PN}-sysroot-libstdc++ = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libstdc++.so* \
"

FILES_${PN}-sysroot-libgcc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${target_base_libdir}/libgcc_s.so* \
"

FILES_${PN}-sysroot-garbage = "\
${base_prefix}/${TARGET_ARCH}/sys-root \
"

# Remaining / ignored files
#/include
#/lib (- /lib/gcc/${TARGET_ARCH})
#/${TARGET_ARCH}/debug-root


CROSS_SYSROOT_MANGLE = "split_sysroot_mangle split_sysroot_mangle_cross"
SDK_SYSROOT_MANGLE = "split_sysroot_mangle split_sysroot_mangle_sdk"
SYSROOT_MANGLE = "${SDK_SYSROOT_MANGLE}"
SYSROOT_MANGLE_recipe-cross	= "${CROSS_SYSROOT_MANGLE}"
SYSROOT_MANGLE_recipe-sdk-cross	= "${CROSS_SYSROOT_MANGLE}"
SYSROOT_MANGLE_recipe-native	= "${CROSS_SYSROOT_MANGLE}"
SPLIT_FUNCS_append += "${SYSROOT_MANGLE}"

# Move the machine sysroot packages into proper target layout
split_sysroot_mangle () {
	# Fixup the layout of the sysroot packages
	for pkg in ${SYSROOT_PACKAGES} ; do
		if [ -d $pkg/${TARGET_ARCH} ] ; then
			(
			echo doing $pkg
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
split_sysroot_mangle[dirs] = "${PKGD}"

# Add symlinks to get sys-root back on stage for internal cross packages
split_sysroot_mangle_cross () {
	ln -s ../../sysroot ${PN}/${TARGET_ARCH}/sys-root
}
split_sysroot_mangle_cross[dirs] = "${PKGD}"

# Add empty sys-root dir in sdk packages
split_sysroot_mangle_sdk () {
	mkdir -p ${PN}/${TARGET_ARCH}/sys-root
}
split_sysroot_mangle_sdk[dirs] = "${PKGD}"
