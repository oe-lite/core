PR = "r2"

S = "${WORKDIR}/build"
B = "${S}"

# Let Crosstool NG manage compiler and linker flags etc.
AWK		= ""
STRIP		= ""
CC		= ""
CPP		= ""
OBJCOPY		= ""
CXX		= ""
AR		= ""
NM		= ""
LD		= ""
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

# Try to avoid messing up sys-root paths
prefix			= ""
sysroot_prefix		= ""
base_prefix		= ""
prefix			= ""
exec_prefix		= ""
base_bindir		= ""
base_sbindir		= ""
base_libdir		= ""
sysconfdir		= ""
localstatedir		= ""
servicedir		= ""
sharedstatedir		= ""
datadir			= ""
infodir			= ""
mandir			= ""
docdir			= ""
bindir			= ""
sbindir			= ""
libdir			= ""
libexecdir		= ""
includedir		= ""

DEFCONFIG = "defconfig.${TARGET_CROSS}"

SRC_URI = "file://${DEFCONFIG}"

# Depend on the right version of the ct-ng tool
DEPENDS = "crosstool-ng-native-${PV}"

DEPENDS_append_bbclassextend-canadian-cross = " ${HOST_CROSS}-toolchain ${TARGET_CROSS}-toolchain"

INHIBIT_DEFAULT_DEPS_bbclassextend-cross = 1
INHIBIT_DEFAULT_DEPS_bbclassextend-sdk-cross = 1

PROVIDES_${PN}_append_bbclassextend-cross += "${TARGET_CROSS}-toolchain"
PROVIDES_${PN}_append_bbclassextend-sdk-cross += "${TARGET_CROSS}-toolchain"

PROVIDES_${PN}-sysroot_append_bbclassextend-cross += "${TARGET_CROSS}-toolchain-sysroot"
PROVIDES_${PN}-sysroot_append_bbclassextend-sdk-cross += "${TARGET_CROSS}-toolchain-sysroot"
RPROVIDES_${PN}-sysroot_append_bbclassextend-cross += "${TARGET_CROSS}-toolchain-sysroot"
RPROVIDES_${PN}-sysroot_append_bbclassextend-sdk-cross += "${TARGET_CROSS}-toolchain-sysroot"

# The ct-ng tools uses $NATIVE_DIR for staying relocateable
export NATIVE_DIR

addtask fetch_tarballs after do_patch before do_configure
do_fetch_tarballs[dirs] = "${B}"
do_fetch_tarballs () {
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${DL_DIR}"%' \
	    -e 's%\(CT_SAVE_TARBALLS_DIR\)=.*%\1=n%' \
	    -e 's%\(CT_SAVE_TARBALLS\)=.*%\1=n%' \
	    -e 's%.*\(CT_ONLY_DOWNLOAD\).*%\1=y%' \
	    -e 's%\(CT_PREFIX_DIR\)=.*%\1="${D}"%' \
	    -e 's%\(CT_INSTALL_DIR_RO\)=.*%\1=n%' \
    	    ${WORKDIR}/${DEFCONFIG} > .config
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

do_configure[dirs] = "${B}"
do_configure () {
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${DL_DIR}"%' \
	    -e 's%\(CT_SAVE_TARBALLS_DIR\)=.*%\1=n%' \
	    -e 's%\(CT_ONLY_DOWNLOAD\)=.*%\1=n%' \
	    -e 's%\(CT_PREFIX_DIR\)=.*%\1="${D}"%' \
	    -e 's%\(CT_INSTALL_DIR_RO\)=.*%\1=n%' \
	    -e 's%\(CT_TARGET_ALIAS\)=.*%\1=""%' \
	    -e 's%\(CT_BUILD\)=.*%\1="${BUILD_ARCH}"%' \
	    -e 's%\(CT_BUILD_PREFIX\)=.*%\1="${BUILD_PREFIX}"%' \
	    -e 's%\(CT_PARALLEL_JOBS\)=.*%\1=4%' \
	    -e 's%.*\(CT_COMP_LIBS_TARGET\).*%\1=y%' \
    	    ${WORKDIR}/${DEFCONFIG} > .config
	# FIXME: CT_COMP_LIBS_TARGET is not really needed for canadian-cross
	ct-ng oldconfig
}

do_configure_prepend_bbclassextend-canadian-cross () {
	sed -e 's%.*\(CT_EXPERIMENTAL\).*%\1=y%' \
	    -e 's%\(CT_CROSS\)=.*%\1=n%' \
	    -e 's%.*\(CT_CANADIAN\).*%\1=y%' \
	    -e 's%.*\(CT_TOOLCHAIN_TYPE\).*%\1="canadian"%' \
	    -e 's%\(CT_HOST\)=.*%\1="${HOST_CROSS}"%' \
	    -e 's%\(CT_HOST_PREFIX\)=.*%\1="${HOST_PREFIX}"%' \
	    -e 's%\(CT_TARGET_PREFIX\)=.*%\1="${TARGET_PREFIX}"%' \
	    -e 's%\(CT_BINUTILS_EXTRA_CONFIG\)=.*%\1="--enable-targets=${TARGET_CROSS}"%' \
    	    ${WORKDIR}/${DEFCONFIG} > ${WORKDIR}/${DEFCONFIG}.tmp
	cat >> ${WORKDIR}/${DEFCONFIG}.tmp <<EOT
CT_HOST="${HOST_ARCH}"
CT_HOST_PREFIX="${HOST_PREFIX}"
CT_TARGET_PREFIX="${TARGET_PREFIX}"
EOT
	cp ${WORKDIR}/${DEFCONFIG}.tmp ${WORKDIR}/${DEFCONFIG}
}

do_compile[dirs] = "${B}"
do_compile () {
	ct-ng build
}

# Stub out do_install
do_install () {
	:
}
do_install_bbclassextend-cross () {
	:
}
do_install_bbclassextend-sdk-cross () {
	:
}
do_install_bbclassextend-canadian-cross () {
	:
}
# And as do_compile actually installs into D, don't clean it on do_install
do_install[cleandirs] = ""

PACKAGES	= "${PN} ${PN}-dbg ${PN}-doc ${PN}-locale"
SYSROOT_PACKAGES= "${PN}-sysroot-dev ${PN}-sysroot-doc ${PN}-sysroot-locale ${PN}-sysroot ${PN}-sysroot-extra"

SYSROOT_DEPENDS = "${PN}-sysroot-dev ${PN}-sysroot-extra"
SYSROOT_DEPENDS_bbclassextend-canadian-cross = ""

DEPENDS_${PN} += "${SYSROOT_DEPENDS}"
DEPENDS_${PN}-sysroot-dev = "${PN}-sysroot"

RDEPENDS_${PN}-sysroot-extra	= "${PN}-sysroot"
RDEPENDS_${PN}-sysroot-locale	= "${PN}-sysroot"
RDEPENDS_${PN}-sysroot-dev	= "${PN}-sysroot"

FILES_${PN} = "\
${base_bindir} \
${base_libdir}/gcc/${TARGET_CROSS} \
${base_libexecdir}/gcc/${TARGET_CROSS} \
${datadir}/aclocal \
${base_prefix}/${TARGET_CROSS}/bin \
${base_prefix}/${TARGET_CROSS}/lib \
"

FILES_${PN}_append_bbclassextend-canadian-cross = "\
${FILES_${PN}-sysroot} \
${FILES_${PN}-sysroot-dev} \
${FILES_${PN}-sysroot-extra} \
"
FILES_${PN}-doc_append_bbclassextend-canadian-cross = "\
${FILES_${PN}-sysroot-doc} \
"
FILES_${PN}-locale_append_bbclassextend-canadian-cross = "\
${FILES_${PN}-sysroot-locale} \
"

FILES_${PN}-sysroot-dev = "\
${base_prefix}/${TARGET_CROSS}/include \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_includedir} \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_libdir}/*.o \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_base_libdir}/*.a \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_libdir}/*.a \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_base_libdir}/*.la \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_libdir}/*.la \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_base_libdir}/ldscripts \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_libdir}/gconv \
"

FILES_${PN}-sysroot-doc = "\
${base_prefix}/${TARGET_CROSS}/sys-root${machine_infodir} \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_mandir} \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_docdir} \
"

FILES_${PN}-sysroot-locale = "\
${base_prefix}/${TARGET_CROSS}/sys-root${machine_datadir}/locale \
${base_prefix}/${TARGET_CROSS}/sys-root${machine_datadir}/i18n \
"

FILES_${PN}-sysroot = "\
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libc.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libc-*.so \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libcrypt.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libcrypt-*.so \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libpthread.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libpthread-*.so \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/ld.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/ld-*.so \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libm.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libm-*.so \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libdl.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libdl-*.so \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libutil.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/libutil-*.so \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/librt.so.* \
${base_prefix}/${TARGET_CROSS}/sys-root/${machine_base_libdir}/librt-*.so \
"

FILES_${PN}-sysroot-extra = "\
${base_prefix}/${TARGET_CROSS}/sys-root \
"

# Remaining / ignored files
#/include
#/lib (- /lib/gcc/${TARGET_CROSS})
#/${TARGET_CROSS}/debug-root


# Move the machine sysroot packages into proper target layout
# and then mend the crosstool-ng-toolchain package so it will
# get back in place on stage
packages_install_sysroot_mangle () {
	for pkg in ${SYSROOT_PACKAGES} ; do
		# Fixup the layout of the sysroot packages
		if [ -d $pkg/${TARGET_CROSS}/sys-root ] ; then
			mv $pkg/${TARGET_CROSS}/sys-root/* $pkg/
			rmdir $pkg/${TARGET_CROSS}/sys-root
		fi
		if [ -d $pkg/${TARGET_CROSS}/include ] ; then
			mkdir -p $pkg/usr/include
			mv $pkg/${TARGET_CROSS}/include/* $pkg/usr/include/
			rmdir $pkg/${TARGET_CROSS}/include
		fi
		if [ -d $pkg/${TARGET_CROSS} ] ; then
			rmdir $pkg/${TARGET_CROSS}
		fi
		# Clone all sdk sysroot package
		cp -a $pkg/* $pkg-sdk/
	done

	mkdir -p ${PN}/lib
	ln -s ../../machine ${PN}/${TARGET_CROSS}/sys-root
	ln -s ./sys-root/usr/include ${PN}/${TARGET_CROSS}/include
}
packages_install_sysroot_mangle[dirs] = "${PKGD}"
PACKAGE_INSTALL_FUNCS_append_bbclassextend-cross = " packages_install_sysroot_mangle"
PACKAGE_INSTALL_FUNCS_append_bbclassextend-sdk-cross = " packages_install_sysroot_mangle"
