INC_PR_append = .0

INHIBIT_DEFAULT_DEPS = 1

S = "${WORKDIR}/${BPN}"
B = "${WORKDIR}/build"

# Let Crosstool NG manage compiler and linker flags
CPPFLAGS=""
CFLAGS=""
CXXFLAGS=""
LDFLAGS=""

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

SRC_URI_append = " file://defconfig.${TARGET_ARCH}"

addtask build_tool after do_unpack before do_configure
do_build_tool[dirs] = "${S}"
do_build_tool () {
	./configure --local
	make
	make install
}

addtask fetch_tarballs after do_build_tool before do_configure
do_fetch_tarballs[dirs] = "${S}"
do_fetch_tarballs () {
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${DL_DIR}"%' \
	    -e 's%\(CT_SAVE_TARBALLS_DIR\)=.*%\1=n%' \
	    -e 's%.*\(CT_ONLY_DOWNLOAD\).*%\1=y%' \
	    -e 's%\(CT_PREFIX_DIR\)=.*%\1="${B}"%' \
	    -e 's%\(CT_INSTALL_DIR_RO\)=.*%\1=n%' \
    	    ${WORKDIR}/defconfig.${TARGET_ARCH} > .config
	./ct-ng build
}

addtask save_tarballs after do_fetch_tarballs before do_configure
do_save_tarballs[dirs] = "${S}"
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
			with open(md5file, "w") as md5out:
				md5out.write(md5data)
			bb.utils.unlockfile(lf)
}

do_configure[dirs] = "${S}"
do_configure () {
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${DL_DIR}"%' \
	    -e 's%\(CT_SAVE_TARBALLS_DIR\)=.*%\1=n%' \
	    -e 's%\(CT_ONLY_DOWNLOAD\)=.*%\1=n%' \
	    -e 's%\(CT_PREFIX_DIR\)=.*%\1="${B}"%' \
	    -e 's%\(CT_INSTALL_DIR_RO\)=.*%\1=n%' \
	    -e 's%\(CT_TARGET_ALIAS\)=.*%\1=""%' \
	    -e 's%\(CT_BUILD\)=.*%\1="${BUILD_ARCH}"%' \
	    -e 's%\(CT_BUILD_PREFIX\)=.*%\1="${BUILD_PREFIX}"%' \
    	    ${WORKDIR}/defconfig.${TARGET_ARCH} > .config
	./ct-ng oldconfig
}

do_compile[dirs] = "${S}"
do_compile () {
	./ct-ng build
}
