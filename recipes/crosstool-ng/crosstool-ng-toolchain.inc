PR = "r0"

INHIBIT_DEFAULT_DEPS = 1

S = "${WORKDIR}/build"
B = "${S}"

# Let Crosstool NG manage compiler and linker flags etc.
AWK		= ""
STRIP		= ""
CC		= ""
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

SRC_URI = "file://defconfig.${TARGET_CROSS}"

# Depend on the right version of the ct-ng tool
DEPENDS = "crosstool-ng-native-${PV}"

PROVIDES_${PN} += "${TARGET_CROSS}/toolchain"

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
    	    ${WORKDIR}/defconfig.${TARGET_CROSS} > .config
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
    	    ${WORKDIR}/defconfig.${TARGET_CROSS} > .config
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

STAGE_PACKAGES	= "${PN} ${PN}-dbg ${PN}-doc"

# FIXME: fixup paths.conf and cross.bbclass to use variables here
FILES_${PN} += "\
/${TARGET_CROSS} \
/bin \
/libexec \
/lib \
/include \
"
