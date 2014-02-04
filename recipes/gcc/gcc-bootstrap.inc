SUMMARY = "Initial GCC for toolchain bootstrapping"

require gcc-common.inc

RECIPE_TYPES = "cross sdk-cross"

C_DEPENDS_TARGET = ""
CXX_DEPENDS_TARGET = ""

CHRPATH_DEPENDS = "host-cross:chrpath"
CHRPATH_TYPES = "HOST"

do_configure() {
	do_configure_gcc \
	--enable-languages=c \
	--disable-shared \
	--without-headers \
	--with-newlib \
	--disable-decimal-float \
	--disable-libgomp \
	--disable-libmudflap \
	--disable-libssp \
	--disable-threads \
	--disable-libatomic \
	--disable-libitm \
	--disable-libsanitizer \
	--disable-libquadmath
}

do_compile_targets = "all-gcc all-target-libgcc"

do_install_targets = "install-gcc install-target-libgcc"

do_install[postfuncs] += "do_install_bootstrap_cleanup"
do_install_bootstrap_cleanup() {
	rm -rf ${D}${datadir}
	find ${D}${exec_prefix}/lib -name libiberty.\* -exec rm {} \;
}

do_split[postfuncs] += "do_split_sysroot_symlink"
do_split_sysroot_symlink() {
	mkdir -p ${PKGD}/${PN}/${TARGET_ARCH}
	ln -s ../../${TARGET_TYPE} ${PKGD}/${PN}/${TARGET_ARCH}/sysroot
}

PACKAGES = "${PN}"
FILES_${PN} = "/"
DEPENDS_${PN} = "binutils ${DEPENDS_HOSTLIB}"

FILES_${PN}[qa] += "allow-libs-in-bindirs"
PROVIDES_${PN}[qa] += "allow-missing-provides:liblto-plugin"

# Local Variables:
# mode: python
# End:
