PR = "r6"

FILESPATH=${@base_set_filespath([\
	"${FILE_DIRNAME}/${PF}",\
	"${FILE_DIRNAME}/${P}",\
	"${FILE_DIRNAME}/${PN}",\
	"${FILE_DIRNAME}/crosstool-ng-${PV}",\
	"${FILE_DIRNAME}/crosstool-ng",\
	"${FILE_DIRNAME}/files",\
], d)}

S = "${WORKDIR}/build"
B = "${S}"

DEFAULT_DEPENDS_recipe-native		= ""
DEFAULT_DEPENDS_recipe-cross		= ""
DEFAULT_DEPENDS_recipe-sdk-cross	= ""

DEPENDS_append_recipe-canadian-cross += "${TUI_DEPENDS}"
TUI_DEPENDS = "ncurses-sdk-dev readline-sdk-dev"
TUI_DEPENDS_host-mingw32 = ""

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

DEFCONFIG_COMMON	= "defconfig.common"

DEFCONFIG_CPU		= "defconfig.${TARGET_CPU}"
DEFCONFIG_CPU_i386	= "defconfig.x86"
DEFCONFIG_CPU_i486	= "defconfig.x86"
DEFCONFIG_CPU_i586	= "defconfig.x86"
DEFCONFIG_CPU_i686	= "defconfig.x86"
DEFCONFIG_CPU_i786	= "defconfig.x86"

DEFCONFIG_OS		= "defconfig.${TARGET_OS}"

SRC_URI = "file://${DEFCONFIG_COMMON} file://${DEFCONFIG_CPU} file://${DEFCONFIG_OS}"

# Depend on the right version of the ct-ng tool
DEPENDS = "crosstool-ng-native-${PV}"

inherit c++

# The ct-ng tools uses $NATIVE_DIR for staying relocateable
export NATIVE_DIR = "${STAGE_DIR}/native"

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

CT_ARCH_ARCH		= ""
CT_ARCH_CPU		= ""
CT_ARCH_TUNE		= ""

CT_ARCH_ARCH_i386	= "${TARGET_CPUTYPE}"
CT_ARCH_ARCH_i486	= "${TARGET_CPUTYPE}"
CT_ARCH_ARCH_i586	= "${TARGET_CPUTYPE}"
CT_ARCH_ARCH_i686	= "${TARGET_CPUTYPE}"
CT_ARCH_ARCH_i786	= "${TARGET_CPUTYPE}"

CT_ARCH_ARCH_x86_64	= "${TARGET_CPUTYPE}"

CT_ARCH_CPU_powerpc	= "${TARGET_CPUTYPE}"

# FIXME: need to do something to support both -march and -mcpu, and at
# the same time handle the fact that config.sub does not suppot armv6,
# armv7 and more.
CT_ARCH_CPU_arm		= "${TARGET_CPUTYPE}"

addtask mangle after do_patch before do_configure
do_mangle[dirs] = "${WORKDIR}"
do_mangle () {

	ct_kernel_version=${_CT_KERNEL_VERSION}`echo ${CT_KERNEL_VERSION}|tr . _`
	ct_binutils_version=${_CT_BINUTILS_VERSION}`echo ${CT_BINUTILS_VERSION}|tr . _`
	ct_cc_version=${_CT_CC_VERSION}`echo ${CT_CC_VERSION}|tr . _`
	ct_libc_version=${_CT_LIBC_VERSION}`echo ${CT_LIBC_VERSION}|tr . _`
	ct_gdb_version=${_CT_GDB_VERSION}`echo ${CT_GDB_VERSION}|tr . _`
	ct_gmp_version=${_CT_GMP_VERSION}`echo ${CT_GMP_VERSION}|tr . _`
	ct_mpfr_version=${_CT_MPFR_VERSION}`echo ${CT_MPFR_VERSION}|tr . _`
	ct_ppl_version=${_CT_PPL_VERSION}`echo ${CT_PPL_VERSION}|tr . _`
	ct_cloog_version=${_CT_CLOOG_VERSION}`echo ${CT_CLOOG_VERSION}|tr . _`
	ct_mpc_version=${_CT_MPC_VERSION}`echo ${CT_MPC_VERSION}|tr . _`
	export ct_kernel_version ct_binutils_version ct_cc_version ct_libc_version ct_gdb_version ct_gmp_version ct_mpfr_version ct_ppl_version ct_cloog_version ct_mpc_version
	echo ct_kernel_version=$ct_kernel_version

	cat ${DEFCONFIG_COMMON} ${DEFCONFIG_CPU} ${DEFCONFIG_OS} | \
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
	    -e 's%.*\(CT_ARCH_FLOAT_HW\).*%\1="${@['n','y'][${TARGET_FPU}]}"%' \
	    -e 's%.*\(CT_ARCH_FLOAT_SW\).*%\1="${@['y','n'][${TARGET_FPU}]}"%' \
    	    -e "s%# \($ct_kernel_version\) is not set%\1=y%" \
	    -e "s%# \($ct_binutils_version\) is not set%\1=y%" \
	    -e "s%# \($ct_cc_version\) is not set%\1=y%" \
	    -e "s%# \($ct_libc_version\) is not set%\1=y%" \
    	    -e "s%\(CT_LIBC_GLIBC_MIN_KERNEL\)=.*%\1="${CT_LIBC_GLIBC_MIN_KERNEL}"%" \
	    -e "s%# \($ct_gdb_version\) is not set%\1=y%" \
	    -e "s%# \($ct_gmp_version\) is not set%\1=y%" \
	    -e "s%# \($ct_mpfr_version\) is not set%\1=y%" \
	    -e "s%# \($ct_ppl_version\) is not set%\1=y%" \
	    -e "s%# \($ct_cloog_version\) is not set%\1=y%" \
	    -e "s%# \($ct_mpc_version\) is not set%\1=y%" \
    	> defconfig

	# FIXME: should we strip the -Wl, off TARGET_LDFLAGS ??
	#    -e 's%\(CT_TARGET_LDFLAGS\)=.*%\1="${TARGET_LDFLAGS}"%' \
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
${base_prefix}/${TARGET_ARCH}/debug-root${machine_bindir}/.debug \
"

FILES_${PN}-sysroot-gdbserver = "\
${base_prefix}/${TARGET_ARCH}/debug-root${machine_bindir}/gdbserver \
${base_prefix}/${TARGET_ARCH}/debug-root${machine_mandir}/man1/gdbserver.1 \
${datadir}/gdb \
"
RDEPENDS_${PN}-sysroot-gdbserver = "${PN}-sysroot-libdl"

FILES_${PN}-sysroot-dbg = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_bindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_bindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_sbindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_sbindir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libexecdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libexecdir}/.debug \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}/gconv/.debug \
"

FILES_${PN}-sysroot-dev = "\
${base_prefix}/${TARGET_ARCH}/include \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_includedir} \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}/*.o \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/*.a \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}/*.a \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/*.la \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}/*.la \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}/*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/ld-linux.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/ldscripts \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}/gconv \
"

FILES_${PN}-sysroot-doc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_infodir} \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_mandir} \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_docdir} \
"

FILES_${PN}-sysroot-locale = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_datadir}/locale \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_datadir}/i18n \
"

# libc can depend on libnss_files libnss_dns
# dropbear libc libcrypt libutil
# ethercat libstdc++ libm libgcc_s
# performance-test-suite librt libm
# libnss_dns libresolv

FILES_${PN}-sysroot-libc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libc.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libc-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/ld.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/ld-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/ld-*.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}64 \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_libdir}64 \
"
# FIXME: the lib64 symlink should be in separate package!

FILES_${PN}-sysroot-libdl = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libdl.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libdl-*.so \
"

FILES_${PN}-sysroot-libcrypt = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libcrypt.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libcrypt-*.so \
"

FILES_${PN}-sysroot-libutil = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libutil-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libnss_dns-*.so \
"

FILES_${PN}-sysroot-libnss-files = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libnss_files-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libnss_files.so.* \
"

FILES_${PN}-sysroot-libnss-dns = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libnss_dns-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libnss_dns.so.* \
"

FILES_${PN}-sysroot-libresolv = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libresolv-*.so \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libresolv.so.* \
"

FILES_${PN}-sysroot-libpthread = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libpthread.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libpthread-*.so \
"

FILES_${PN}-sysroot-libm = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libm.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libm-*.so \
"

FILES_${PN}-sysroot-librt = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/librt.so.* \
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/librt-*.so \
"

FILES_${PN}-sysroot-libstdc++ = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libstdc++.so* \
"

FILES_${PN}-sysroot-libgcc = "\
${base_prefix}/${TARGET_ARCH}/sys-root${machine_base_libdir}/libgcc_s.so* \
"

FILES_${PN}-sysroot-garbage = "\
${base_prefix}/${TARGET_ARCH}/sys-root \
"

# Remaining / ignored files
#/include
#/lib (- /lib/gcc/${TARGET_ARCH})
#/${TARGET_ARCH}/debug-root


CROSS_SYSROOT_MANGLE = "package_install_sysroot_mangle package_install_sysroot_mangle_cross"
SDK_SYSROOT_MANGLE = "package_install_sysroot_mangle package_install_sysroot_mangle_sdk"
SYSROOT_MANGLE = "${SDK_SYSROOT_MANGLE}"
SYSROOT_MANGLE_recipe-cross	= "${CROSS_SYSROOT_MANGLE}"
SYSROOT_MANGLE_recipe-sdk-cross	= "${CROSS_SYSROOT_MANGLE}"
SYSROOT_MANGLE_recipe-native	= "${CROSS_SYSROOT_MANGLE}"
PACKAGE_INSTALL_FUNCS_append += "${SYSROOT_MANGLE}"

# Move the machine sysroot packages into proper target layout
package_install_sysroot_mangle () {
	# Fixup the layout of the sysroot packages
	for pkg in ${SYSROOT_PACKAGES} ; do
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
			rm -f include
			if [ -d include ] ; then
				mkdir -p ../${machine_includedir}
				mv include/* ../${machine_includedir}
				rmdir include
			fi
			rm -f lib
			if [ -d lib ] ; then
				mkdir -p ../${machine_libdir}
				mv lib/* ../${machine_libdir}
				rmdir lib
			fi
			cd ..
			rmdir ${TARGET_ARCH}
			)
		fi
	done
	ln -s ./sys-root/usr/include ${PN}/${TARGET_ARCH}/include
}
package_install_sysroot_mangle[dirs] = "${PKGD}"

# Add symlinks to get sys-root back on stage for internal cross packages
package_install_sysroot_mangle_cross () {
	ln -s ../../sysroot ${PN}/${TARGET_ARCH}/sys-root
}
package_install_sysroot_mangle_cross[dirs] = "${PKGD}"

# Add empty sys-root dir in sdk packages
package_install_sysroot_mangle_sdk () {
	mkdir -p ${PN}/${TARGET_ARCH}/sys-root
}
package_install_sysroot_mangle_sdk[dirs] = "${PKGD}"
