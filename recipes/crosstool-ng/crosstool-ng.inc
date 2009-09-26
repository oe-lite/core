INC_PR = ".0"

inherit cross

INHIBIT_DEFAULT_DEPS = 1

S = "${WORKDIR}/${PN}"

# Let Crosstool NG manage compiler and linker flags
CPPFLAGS=""
CFLAGS=""
CXXFLAGS=""
LDFLAGS=""

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
	    -e 's%.*\(CT_ONLY_DOWNLOAD\).*%\1=y%' \
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

do_configure () {
	cd ${S}
	sed -e 's%\(CT_LOCAL_TARBALLS_DIR\)=.*%\1="${DL_DIR}"%' \
	    -e 's%.*\(CT_SAVE_TARBALLS_DIR\).*%\1=n%' \
	    -e 's%\(CT_PREFIX_DIR\)=.*%\1="${STAGING_DIR}/${TARGET_ARCH}"%' \
	    -e 's%\(CT_TARGET_ALIAS\)=.*%\1="${TARGET_ARCH}"%' \
    	    ${WORKDIR}/defconfig.${TARGET_ARCH} > .config
	./ct-ng oldconfig
}

do_compile () {
	cd ${S}
	./ct-ng build
}

# CT_TARGET_CFLAGS
# CT_TARGET_LDFLAGS
