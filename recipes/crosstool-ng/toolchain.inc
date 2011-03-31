FILESPATHPKG = "${PF}:${P}:${PN}:${BP}:${BPN}:toolchain-${PV}:toolchain-${@'.'.join('${PV}'.split('.')[:2])}:toolchain:files"

RECIPE_OPTIONS += "toolchain_cc toolchain_cc_version"
# Remember to configure defaults for these in the gcc_*.bb file
CT_CC		= "${RECIPE_OPTION_toolchain_cc}"
CT_CC_VERSION	= "${RECIPE_OPTION_toolchain_cc_version}"

RECIPE_OPTIONS += "toolchain_libc toolchain_libc_version"
RECIPE_OPTIONS += "toolchain_mingwrt_version"
# Remember to configure defaults for these in the gcc_*.bb file
CT_LIBC			= "${RECIPE_OPTION_toolchain_libc}"
CT_LIBC_mingw32		= "mingw"
CT_LIBC_VERSION		= "${RECIPE_OPTION_toolchain_libc_version}"
CT_LIBC_VERSION_mingw32 = "${RECIPE_OPTION_toolchain_mingwrt_version}"

# *sigh* why don't eglibc use releases?
RECIPE_OPTIONS += "toolchain_libc_eglibc_revision"
# Remember to configure defaults for these in the gcc_*.bb file
CT_EGLIBC_REVISION = "${RECIPE_OPTION_toolchain_libc_eglibc_revision}"

CT_KERNEL		= "linux"
CT_KERNEL_mingw32	= "mingw32"

RECIPE_OPTIONS += "toolchain_kernel_version_machine"
RECIPE_OPTIONS += "toolchain_kernel_version_sdk"
RECIPE_OPTIONS += "toolchain_kernel_version_build"
RECIPE_OPTIONS += "toolchain_w32api_version"
# Remember to configure defaults for these in the gcc_*.bb file

MACHINE_CT_KERNEL_VERSION = "${RECIPE_OPTION_toolchain_kernel_version_machine}"
CT_KERNEL_VERSION			= "${MACHINE_CT_KERNEL_VERSION}"

SDK_CT_KERNEL_VERSION         = "${RECIPE_OPTION_toolchain_kernel_version_sdk}"
SDK_CT_KERNEL_VERSION_mingw32 = "${RECIPE_OPTION_toolchain_w32api_version}"
CT_KERNEL_VERSION_recipe-sdk-cross	= "${SDK_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION_recipe-sdk		= "${SDK_CT_KERNEL_VERSION}"

BUILD_CT_KERNEL_VERSION = "${RECIPE_OPTION_toolchain_kernel_version_build}"
CT_KERNEL_VERSION_recipe-native		= "${BUILD_CT_KERNEL_VERSION}"

RECIPE_OPTIONS += "toolchain_min_kernel_machine"
RECIPE_OPTIONS += "toolchain_min_kernel_sdk"
RECIPE_OPTIONS += "toolchain_min_kernel_build"
# Remember to configure defaults for these in the gcc_*.bb file
CT_LIBC_GLIBC_MIN_KERNEL_VERSION = "${RECIPE_OPTION_toolchain_min_kernel_machine}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION_recipe-sdk-cross = "${RECIPE_OPTION_toolchain_min_kernel_sdk}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION_recipe-sdk = "${RECIPE_OPTION_toolchain_min_kernel_sdk}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION_recipe-native	= "${RECIPE_OPTION_toolchain_min_kernel_build}"

RECIPE_OPTIONS		+= "toolchain_binutils_version"
CT_BINUTILS_VERSION	= "${RECIPE_OPTION_toolchain_binutils_version}"

RECIPE_OPTIONS		+= "toolchain_gdb_version"
CT_GDB_VERSION		= "${RECIPE_OPTION_toolchain_gdb_version}"

RECIPE_OPTIONS		+= "toolchain_gmp_version"
CT_GMP_VERSION		= "${RECIPE_OPTION_toolchain_gmp_version}"

RECIPE_OPTIONS		+= "toolchain_mpfr_version"
CT_MPFR_VERSION		= "${RECIPE_OPTION_toolchain_mpfr_version}"

RECIPE_OPTIONS		+= "toolchain_ppl_version"
CT_PPL_VERSION		= "${RECIPE_OPTION_toolchain_ppl_version}"

RECIPE_OPTIONS		+= "toolchain_cloog_version"
CT_CLOOG_VERSION	= "${RECIPE_OPTION_toolchain_cloog_version}"

RECIPE_OPTIONS		+= "toolchain_mpc_version"
CT_MPC_VERSION		= "${RECIPE_OPTION_toolchain_mpc_version}"

RECIPE_OPTIONS		+= "toolchain_libelf_version"
CT_LIBELF_VERSION	= "${RECIPE_OPTION_toolchain_libelf_version}"

# FIXME: come up with a more elegant solution. if not before, it then when
# fx. uclibc or eglibc is used, or even more, if llvm compiler is added
TOOLCHAIN_VERSION		= "${CT_CC}${CT_CC_VERSION}"
TOOLCHAIN_VERSION_append	= "-${CT_LIBC}${CT_LIBC_VERSION}"

PR = "${TOOLCHAIN_VERSION}"

# Depend on the right version of the ct-ng tool
DEPENDS = "crosstool-ng-native-${PV}"

S = "${WORKDIR}/build"
B = "${S}"

DEFAULT_DEPENDS_recipe-native		= ""
DEFAULT_DEPENDS_recipe-cross		= ""
DEFAULT_DEPENDS_recipe-sdk-cross	= ""

DEPENDS += "${TUI_DEPENDS}"
TUI_DEPENDS				= ""
TUI_DEPENDS_recipe-machine		= "libtermcap${RE} libreadline${RE}"
SDK_TUI_DEPENDS				= "libtermcap-sdk libreadline-sdk"
SDK_TUI_DEPENDS_host-mingw32		= ""
TUI_DEPENDS_recipe-sdk			= "${SDK_TUI_DEPENDS}"
TUI_DEPENDS_recipe-canadian-cross	= "${SDK_TUI_DEPENDS}"

SYSROOT_RE = ""
SYSROOT_RE_append_recipe-native		= "-native"
SYSROOT_RE_append_recipe-machine	= "-machine-garbage"
SYSROOT_RE_append_recipe-sdk-cross	= "-sdk"
SYSROOT_RE_append_recipe-sdk		= "-sdk-garbage"
SYSROOT_RE_append_recipe-canadian-cross	= "-canadian-garbage"

# FIXME: allow machine/sdk/canadian-cross toolchains are built
# statically, to make it more robust against host machine differences

# FIXME: this looks REALLY wrong!
DEPENDS_append_recipe-canadian-cross += "\
${TARGET_ARCH}/sysroot-libdl \
${TARGET_ARCH}/sysroot-libpthread \
${TARGET_ARCH}/sysroot-libm \
"

# Trick install_strip to use installed strip and objcopy
TARGET_STRIP	= "${D}/bin/${TARGET_PREFIX}strip"
TARGET_OBJCOPY	= "${D}/bin/${TARGET_PREFIX}objcopy"

# Let Crosstool NG manage compiler and linker flags etc.
AWK		= ""
CC		= ""
CPP		= ""
CXX		= ""
F77		= ""
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
export CT_PARALLEL_JOBS	?= "1"
CT_LOAD			= "0"

_CT_KERNEL_V		= "CT_KERNEL_V"
_CT_KERNEL_V_mingw32	= "CT_W32API_V"
_CT_BINUTILS_V		= "CT_BINUTILS_V"
_CT_CC_V		= "CT_CC_V"
_CT_LIBC_V		= "CT_LIBC_V"
_CT_LIBC_V_mingw32	= "CT_MINGWRT_V"
_CT_GDB_V		= "CT_GDB_V"
_CT_GMP_V		= "CT_GMP_V"
_CT_MPFR_V		= "CT_MPFR_V"
_CT_PPL_V		= "CT_PPL_V"
_CT_CLOOG_V		= "CT_CLOOG_V"
_CT_MPC_V		= "CT_MPC_V"
_CT_LIBELF_V		= "CT_LIBELF_V"

CT_ARCH_ARCH			= "${TARGET_MARCH}"
CT_ARCH_CPU			= "${TARGET_MCPU}"
CT_ARCH_TUNE			= "${TARGET_MTUNE}"

# FIXME: add crosstool-ng and OE-lite support for x86 -mfpmath option

CT_LIBC_GLIBC_FORCE_UNWIND			= "n"
CT_LIBC_GLIBC_FORCE_UNWIND_linux-gnu		= "y"
CT_LIBC_GLIBC_FORCE_UNWIND_linux-gnueabi	= "y"

DEPENDS += "${TOOLCHAIN_DEFAULT_DEPENDS}"
TOOLCHAIN_DEFAULT_DEPENDS = ""
python () {
    if (d.getVar("RECIPE_TYPE", True) == "cross" and
        d.getVar("MACHINE_CT_KERNEL_VERSION", True) == "custom"):
        d.setVar("TOOLCHAIN_DEFAULT_DEPENDS", "linux-headers")
}

AUTO_LIB_PACKAGES = "\
  libgcc libdl libstdc++ libsupc++ libresolv libutil libcrypt libpthread \
  libm librt libanl libBrokenLocale libnsl libmemusage \
  libpcprofile libSegFault \
  libthread_db libnss_files libnss_dns libnss_compat \
  libnss_nis libnss_nisplus libnss_hesiod libbfd \
"

AUTO_PACKAGE_FUNCS += "toolchain_auto_packages_func"
def toolchain_auto_packages_func (d):
    pn = d.getVar("PN", True)
    auto_lib_packages = d.getVar("AUTO_LIB_PACKAGES", False).split()
    lib_packages = []
    def get_extra_files(pkg):
        extra_files = d.getVar("EXTRA_FILES_" + pkg, False)
        if extra_files:
            return " " + extra_files
        return ""
    for lib in auto_lib_packages:
        pkg = "%s-sysroot-%s"%(pn, lib.replace("_", "-").lower())
        lib_packages += [ pkg, pkg + "-dev" ]
        extra_files = get_extra_files(pkg)
        d.setVar("FILES_" + pkg,
                 "${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/%s.so "%(lib) +
                 "${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/%s.so.* "%(lib) +
                 "${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/%s-*.so "%(lib) +
                 extra_files)
        pkg += "-dev"
        extra_files = get_extra_files(pkg)
        d.setVar("FILES_" + pkg,
                 "${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/%s.so "%(lib) +
                 "${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/%s.a "%(lib) +
                 "${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/%s_nonshared.a "%(lib) +
                 "${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/%s.la "%(lib) +
                 extra_files)
    sysroot_packages = (lib_packages +
                        (d.getVar("SYSROOT_PACKAGES", False) or "").split())
    d.setVar("SYSROOT_PACKAGES", " ".join(sysroot_packages))

addtask mangle after do_patch before do_configure
do_mangle[dirs] = "${SRCDIR}"
do_mangle () {

	if [ "${CT_KERNEL_VERSION}" != "custom" ]; then
		ct_kernel_version=${_CT_KERNEL_V}_`echo ${CT_KERNEL_VERSION}|tr . _`=y
	else
		ct_kernel_version="# ${_CT_KERNEL_V}_ is not set"
	fi
	ct_binutils_version=${_CT_BINUTILS_V}_`echo ${CT_BINUTILS_VERSION}|tr . _`=y
	ct_cc_version=${_CT_CC_V}_`echo ${CT_CC_VERSION}|tr . _`=y
	ct_libc_version=${_CT_LIBC_V}_`echo ${CT_LIBC_VERSION}|tr . _`=y
	ct_gdb_version=${_CT_GDB_V}_`echo ${CT_GDB_VERSION}|tr . _`=y
	ct_gmp_version=${_CT_GMP_V}_`echo ${CT_GMP_VERSION}|tr . _`=y
	ct_mpfr_version=${_CT_MPFR_V}_`echo ${CT_MPFR_VERSION}|tr . _`=y
	ct_ppl_version=${_CT_PPL_V}_`echo ${CT_PPL_VERSION}|tr . _`=y
	ct_cloog_version=${_CT_CLOOG_V}_`echo ${CT_CLOOG_VERSION}|tr . _`=y
	ct_mpc_version=${_CT_MPC_V}_`echo ${CT_MPC_VERSION}|tr . _`=y
	ct_libelf_version=${_CT_LIBELF_V}_`echo ${CT_LIBELF_VERSION}|tr . _`=y
	export ct_kernel_version ct_binutils_version ct_cc_version ct_libc_version ct_gdb_version ct_gmp_version ct_mpfr_version ct_ppl_version ct_cloog_version ct_mpc_version ct_libelf_version

	cat defconfig.misc ${DEFCONFIG_CPU} defconfig.toolchain ${DEFCONFIG_OS} | \
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${DL_DIR}"%' \
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
    	    -e "s%# __${_CT_KERNEL_V}_%$ct_kernel_version%" \
    	    -e "s%# __${_CT_BINUTILS_V}_%$ct_binutils_version%" \
    	    -e "s%# __${_CT_CC_V}_%$ct_cc_version%" \
    	    -e "s%# __${_CT_LIBC_V}_%$ct_libc_version%" \
            -e "s%.*\(CT_LIBC_GLIBC_FORCE_UNWIND\).*%\1=${CT_LIBC_GLIBC_FORCE_UNWIND}%" \
    	    -e "s%# __${_CT_GDB_V}_%$ct_gdb_version%" \
    	    -e "s%# __${_CT_GMP_V}_%$ct_gmp_version%" \
    	    -e "s%# __${_CT_MPFR_V}_%$ct_mpfr_version%" \
    	    -e "s%# __${_CT_PPL_V}_%$ct_ppl_version%" \
    	    -e "s%# __${_CT_CLOOG_V}_%$ct_cloog_version%" \
    	    -e "s%# __${_CT_MPC_V}_%$ct_mpc_version%" \
    	    -e "s%# __${_CT_LIBELF_V}_%$ct_libelf_version%" \
    	> defconfig

	if [ CT_KERNEL_VERSION != CT_LIBC_GLIBC_MIN_KERNEL_VERSION ]; then
		mv defconfig defconfig.tmp
		cat defconfig.tmp |
		   sed -e 's%CT_LIBC_GLIBC_KERNEL_VERSION_AS_HEADERS=y%CT_LIBC_GLIBC_KERNEL_VERSION_AS_HEADERS=n%' \
		       -e 's%\# CT_LIBC_GLIBC_KERNEL_VERSION_CHOSEN is not set%CT_LIBC_GLIBC_KERNEL_VERSION_CHOSEN=y%' \
		       -e "s%\(CT_LIBC_GLIBC_MIN_KERNEL_VERSION\)=.*%\1=\"${CT_LIBC_GLIBC_MIN_KERNEL_VERSION}\"%" \
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
do_fetch_tarballs[cleandirs] = "${B}"
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
	${DOT_CONFIG_MANGLING} <${SRCDIR}/defconfig > .config
	ct-ng oldconfig
}

addtask configure_qa after do_configure
do_configure_qa[dirs] = "${B}"
do_configure_qa () {
	fail=0

	if [ "${CT_KERNEL_VERSION}" != "custom" ]; then
		kernel_version=`grep ${_CT_KERNEL_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$kernel_version" != "${CT_KERNEL_VERSION}" ]; then
			oewarn "CT_KERNEL_VERSION = $kernel_version (should be ${CT_KERNEL_VERSION})"
			fail=1
		else
			oenote "CT_KERNEL_VERSION = $kernel_version"
		fi
	fi

	binutils_version=`grep ${_CT_BINUTILS_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
	if [ "$binutils_version" != "${CT_BINUTILS_VERSION}" ]; then
		oewarn "CT_BINUTILS_VERSION = $binutils_version (should be ${CT_BINUTILS_VERSION})"
		fail=1
	else
		oenote "CT_BINUTILS_VERSION = $binutils_version"
	fi

	cc_version=`grep ${_CT_CC_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
	if [ "$cc_version" != "${CT_CC_VERSION}" ]; then
		oewarn "CT_CC_VERSION = $cc_version (should be ${CT_CC_VERSION})"
		fail=1
	else
		oenote "CT_CC_VERSION = $cc_version"
	fi

	libc_version=`grep ${_CT_LIBC_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
	if [ "$libc_version" != "${CT_LIBC_VERSION}" ]; then
		oewarn "CT_LIBC_VERSION = $libc_version (should be ${CT_LIBC_VERSION})"
		fail=1
	else
		oenote "CT_LIBC_VERSION = $libc_version"
	fi

	if grep "CT_KERNEL_linux=y" .config >/dev/null; then

		gdb_version=`grep ${_CT_GDB_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$gdb_version" != "${CT_GDB_VERSION}" ]; then
			oewarn "CT_GDB_VERSION = $gdb_version (should be ${CT_GDB_VERSION})"
			fail=1
		else
			oenote "CT_GDB_VERSION = $gdb_version"
		fi

	fi

	if grep "CT_GMP_NEEDED=y" .config >/dev/null; then
		gmp_version=`grep ${_CT_GMP_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$gmp_version" != "${CT_GMP_VERSION}" ]; then
			oewarn "CT_GMP_VERSION = $gmp_version (should be ${CT_GMP_VERSION})"
			fail=1
		else
			oenote "CT_GMP_VERSION = $gmp_version"
		fi
	fi

	if grep "CT_MPFR_NEEDED=y" .config >/dev/null; then
		mpfr_version=`grep ${_CT_MPFR_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$mpfr_version" != "${CT_MPFR_VERSION}" ]; then
			oewarn "CT_MPFR_VERSION = $mpfr_version (should be ${CT_MPFR_VERSION})"
			fail=1
		else
			oenote "CT_MPFR_VERSION = $mpfr_version"
		fi
	fi

	if grep "CT_PPL_NEEDED=y" .config >/dev/null; then
		ppl_version=`grep ${_CT_PPL_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$ppl_version" != "${CT_PPL_VERSION}" ]; then
			oewarn "CT_PPL_VERSION = $ppl_version (should be ${CT_PPL_VERSION})"
			fail=1
		else
			oenote "CT_PPL_VERSION = $ppl_version"
		fi
	fi

	if grep "CT_CLOOG_NEEDED=y" .config >/dev/null; then
		cloog_version=`grep ${_CT_CLOOG_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$cloog_version" != "${CT_CLOOG_VERSION}" ]; then
			oewarn "CT_CLOOG_VERSION = $cloog_version (should be ${CT_CLOOG_VERSION})"
			fail=1
		else
			oenote "CT_CLOOG_VERSION = $cloog_version"
		fi
	fi

	if grep "CT_MPC_NEEDED=y" .config >/dev/null; then
		mpc_version=`grep ${_CT_MPC_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$mpc_version" != "${CT_MPC_VERSION}" ]; then
			oewarn "CT_MPC_VERSION = $mpc_version (should be ${CT_MPC_VERSION})"
			fail=1
		else
			oenote "CT_MPC_VERSION = $mpc_version"
		fi
	fi

	if grep "CT_LIBELF_NEEDED=y" .config >/dev/null; then
		libelf_version=`grep ${_CT_LIBELF_V}ERSION .config|awk -F= '{ print $2 }'|tr -d '"'`
		if [ "$libelf_version" != "${CT_LIBELF_VERSION}" ]; then
			oewarn "CT_LIBELF_VERSION = $libelf_version (should be ${CT_LIBELF_VERSION})"
			fail=1
		else
			oenote "CT_LIBELF_VERSION = $libelf_version"
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
    mv ${TARGET_ARCH}/sysroot${target_base_libdir}/*.la \
       ${TARGET_ARCH}/sysroot${target_base_libdir}/*.a \
       ${TARGET_ARCH}/sysroot${target_libdir}/ || true
}

# We always build all packages, so care must be taken to choose the
# right sysroot packages as there can be multiple builds providing
# (almost) the same
PACKAGES = "${PN}-dbg ${PN} ${PN}-doc ${PN}-locale ${PN}-gdb"

PROVIDES_${PN} = "toolchain${RE}"
PROVIDES_${PN}_append_recipe-cross	+= "${TARGET_ARCH}/toolchain"
PROVIDES_${PN}_append_recipe-sdk-cross	+= "${TARGET_ARCH}/toolchain"
DEPENDS_${PN} = "${PN}-sysroot-dev"

DEPENDS_${PN}-sysroot-libnss-dns-dev	= "${PN}-sysroot-libresolv-dev"
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

FILES_${PN}-doc += "\
${base_prefix}/build.log* \
"

FILES_${PN}-dbg += "\
${base_prefix}/${TARGET_ARCH}/bin/.debug \
${libexecdir}/gcc/${TARGET_ARCH}/${RECIPE_OPTION_toolchain_cc_version}/.debug \
${libexecdir}/gcc/${TARGET_ARCH}/${RECIPE_OPTION_toolchain_cc_version}/*/.debug \
"

SYSROOT_PACKAGES += "${PN}-sysroot-libc"
FILES_${PN}-sysroot-libc = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/libc.so.* \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/libc-*.so \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/ld.so.* \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/ld-*.so \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/ld-*.so.* \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}64 \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}64 \
"

SYSROOT_PACKAGES += "${PN}-sysroot-libc-dev"
# FIXME: the lib64 symlink should be in separate package!
FILES_${PN}-sysroot-libc-dev = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/libc.so \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/libc.a \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/libc_nonshared.a \
"

SYSROOT_PACKAGES += "${PN}-sysroot-gdbserver-dbg"
FILES_${PN}-sysroot-gdbserver-dbg = "\
${base_prefix}/${TARGET_ARCH}/debug-root${target_bindir}/.debug \
"

SYSROOT_PACKAGES += "${PN}-sysroot-gdbserver"
FILES_${PN}-sysroot-gdbserver = "\
${base_prefix}/${TARGET_ARCH}/debug-root${target_bindir}/gdbserver \
${base_prefix}/${TARGET_ARCH}/debug-root${target_mandir}/man1/gdbserver.1 \
${datadir}/gdb \
"
RDEPENDS_${PN}-sysroot-gdbserver = "${PN}-sysroot-libdl"

SYSROOT_PACKAGES += "${PN}-sysroot-dbg"
FILES_${PN}-sysroot-dbg = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_bindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_bindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_sbindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_sbindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libexecdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libexecdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/gconv/.debug \
"

SYSROOT_PACKAGES += "${PN}-sysroot-dev"
FILES_${PN}-sysroot-dev = "\
${base_prefix}/${TARGET_ARCH}/include \
${base_prefix}/${TARGET_ARCH}/sysroot${target_includedir} \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/*.a \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/*.o \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/*.py \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/*.la \
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/ldscripts \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/*.o \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/*.a \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/*.la \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/*.so \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/gconv \
${base_prefix}/${TARGET_ARCH}/sysroot/mingw \
"
DEPENDS_${PN}-sysroot-dev  = "${PN}-sysroot-libc-dev ${PN}-sysroot-libgcc-dev"
RDEPENDS_${PN}-sysroot-dev = "${PN}-sysroot-libc-dev ${PN}-sysroot-libgcc-dev"

FILES_${PN}-sysroot-dev_append_mingw32 = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_bindir}/*.dll \
"

SYSROOT_PACKAGES += "${PN}-sysroot-doc"
FILES_${PN}-sysroot-doc = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_infodir} \
${base_prefix}/${TARGET_ARCH}/sysroot${target_mandir} \
${base_prefix}/${TARGET_ARCH}/sysroot${target_docdir} \
"

# Hackeydihack.... should instead get all sysroot doc in target_docdir
FILES_${PN}-sysroot-doc_append_mingw32 = "\
${base_prefix}/${TARGET_ARCH}/sysroot/doc/runtime \
"

SYSROOT_PACKAGES += "${PN}-sysroot-locale"
FILES_${PN}-sysroot-locale = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_datadir}/locale \
${base_prefix}/${TARGET_ARCH}/sysroot${target_datadir}/i18n \
"

EXTRA_FILES_${PN}-sysroot-libgcc = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/libgcc_s.so.* \
"

EXTRA_FILES_${PN}-sysroot-libgcc-dev = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_libdir}/libgcc_s.so \
"

EXTRA_FILES_${PN}-sysroot-libm-dev = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/libieee.a \
"

EXTRA_FILES_${PN}-sysroot-libbfd = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/libbfd-*.so \
${base_prefix}/${TARGET_ARCH}/sysroot${target_libdir}/libbfd.so"

SYSROOT_PACKAGES += "${PN}-sysroot-nscd"
FILES_${PN}-sysroot-nscd = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_sbindir}/nscd"
RPROVIDES_${PN}-sysroot-nscd = "util/rpcgen${SYSROOT_RE} util/nscd${SYSROOT_RE}"

SYSROOT_PACKAGES += "${PN}-sysroot-rpc"
FILES_${PN}-sysroot-rpc = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_bindir}/rpcgen \
${base_prefix}/${TARGET_ARCH}/sysroot${target_sbindir}/rpcinfo \
${base_prefix}/${TARGET_ARCH}/sysroot${target_sysconfdir}/rpc"
RPROVIDES_${PN}-sysroot-rpc = "util/rpcgen${SYSROOT_RE} util/rpcinfo${SYSROOT_RE}"

SYSROOT_PACKAGES += "${PN}-sysroot-ldconfig"
FILES_${PN}-sysroot-ldconfig = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_base_sbindir}/ldconfig"
RPROVIDES_${PN}-sysroot-ldconfig = "util/ldconfig${SYSROOT_RE}"

SYSROOT_PACKAGES += "${PN}-sysroot-ldd"
FILES_${PN}-sysroot-ldd = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_bindir}/ldd"
RPROVIDES_${PN}-sysroot-ldd = "util/ldd${SYSROOT_RE}"

SYSROOT_PACKAGES += "${PN}-sysroot-catchsegv"
FILES_${PN}-sysroot-catchsegv = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_bindir}/catchsegv"
RPROVIDES_${PN}-sysroot-catchsegv = "util/catchsegv${SYSROOT_RE}"

SYSROOT_PACKAGES += "${PN}-sysroot-sprof"
FILES_${PN}-sysroot-sprof = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_bindir}/sprof"
RPROVIDES_${PN}-sysroot-sprof = "util/sprof${SYSROOT_RE}"

SYSROOT_PACKAGES += "${PN}-sysroot-timezone-utils"
FILES_${PN}-sysroot-timezone-utils = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_bindir}/tzselect \
${base_prefix}/${TARGET_ARCH}/sysroot${target_sbindir}/zdump \
${base_prefix}/${TARGET_ARCH}/sysroot${target_sbindir}/zic \
${base_prefix}/${TARGET_ARCH}/sysroot${target_datadir}/zoneinfo \
"
RPROVIDES_${PN}-sysroot-timezone-utils = "\
    util/tzselect${SYSROOT_RE} util/zdump${SYSROOT_RE} util/zic${SYSROOT_RE} util/zoneinfo${SYSROOT_RE}"

SYSROOT_PACKAGES += "${PN}-sysroot-iconv-utils"
FILES_${PN}-sysroot-iconv-utils = "\
${base_prefix}/${TARGET_ARCH}/sysroot${target_bindir}/iconv \
${base_prefix}/${TARGET_ARCH}/sysroot${target_sbindir}/iconvconfig"
RPROVIDES_${PN}-sysroot-iconv-utils = "util/iconv${SYSROOT_RE} util/iconvconfig${SYSROOT_RE}"

# throw everything else in this garbage package, which is to be considered a WIP package aimed at being empty
SYSROOT_PACKAGES += "${PN}-sysroot-garbage"
FILES_${PN}-sysroot-garbage = "\
${base_prefix}/${TARGET_ARCH}/sysroot \
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
			cd $pkg/${TARGET_ARCH}
			if [ -d debug-root ] ; then
				mv debug-root/* ../
				rmdir debug-root
			fi
			if [ -d sysroot ] ; then
				mv sysroot/* ../
				rmdir sysroot
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
	ln -s ./sysroot/usr/include ${PN}/${TARGET_ARCH}/include
}
split_sysroot_mangle[dirs] = "${PKGD}"

split_sysroot_mangle_append_mingw32 () {
    # Move object files (*.o) to usr/lib so that ld can find them through
    # the mingw/lib dir (mingw symlinks to /usr)
    for pkg in ${SYSROOT_PACKAGES} ; do
        if [ -d $pkg/lib ] ; then
            for f in $pkg/lib/*.o ; do
		test -f $f && mv $f $pkg${target_libdir}/
            done
	fi
    done
}

# Add symlinks to get sysroot back on stage for internal cross packages
split_sysroot_mangle_cross () {
	ln -s ../../sysroot ${PN}/${TARGET_ARCH}/sysroot
}
split_sysroot_mangle_cross[dirs] = "${PKGD}"

# Add empty sysroot dir in sdk packages
split_sysroot_mangle_sdk () {
	mkdir -p ${PN}/${TARGET_ARCH}/sysroot
}
split_sysroot_mangle_sdk[dirs] = "${PKGD}"

inherit libtool
LIBTOOL_DEPENDS = ""
LIBTOOL_FIXUP_SEARCH_DIRS += "\
${D}/${TARGET_ARCH}/sysroot${target_libdir} \
${D}/${TARGET_ARCH}/sysroot${target_base_libdir}"
LIBTOOL_FIXUP_STRIP_DIRS += "${D}/${TARGET_ARCH}/lib"

FIXUP_FUNCS =+ "toolchain_lafile_fixup"
toolchain_lafile_fixup () {
    for lafile in ${D}/${TARGET_ARCH}/sysroot${target_libdir}/*.la ; do
        sed -e "s:-L`readlink -f ${B}`/targets/${TARGET_ARCH}/[^ ']* *::" \
            -i $lafile
    done
}
