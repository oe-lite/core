# -*- mode:python; -*-

# as do_compile actually installs into D, don't clean it on do_install
do_install[cleandirs] = ""
do_install[dirs] = "${D}"

OBJCOPY:TARGET_OS_mingw32 = ""

# Trick install_strip to use installed strip and objcopy
TARGET_STRIP	= "${D}/bin/${TARGET_PREFIX}strip"
TARGET_OBJCOPY	= "${D}/bin/${TARGET_PREFIX}objcopy"

# everything is already installed in do_compile, but let's rearrange it a bit
do_install () {
    mv ${TARGET_ARCH}/sysroot${target_base_libdir}/*.la \
       ${TARGET_ARCH}/sysroot${target_base_libdir}/*.a \
       ${TARGET_ARCH}/sysroot${target_libdir}/ || true

    mkdir -p ${TARGET_ARCH}/debug-root${target_bindir}/
    mv ${TARGET_ARCH}/debug-root${target_prefix}${target_base_bindir}/* \
        ${TARGET_ARCH}/debug-root${target_bindir}/ || true

    mv ${TARGET_ARCH}/debug-root${target_prefix}${target_datadir} \
        ${TARGET_ARCH}/debug-root${target_base_prefix}/ || true

    mv ${TARGET_ARCH}/debug-root${target_prefix}${target_sysconfdir} \
        ${TARGET_ARCH}/debug-root${target_base_prefix}/ || true

    [ -d share ] \
        && [ "/share" != "${datadir}" ] \
        && install -d ${D}${datadir} \
        && mv share/* ${D}${datadir}/

    install -m 0644 ${B}/.config ${PN}-config
}

inherit libtool
LIBTOOL_DEPENDS = ""
LIBTOOL_FIXUP_SEARCH_DIRS += "\
${D}/${TARGET_ARCH}/sysroot${target_libdir} \
${D}/${TARGET_ARCH}/sysroot${target_base_libdir}"
LIBTOOL_FIXUP_STRIP_DIRS =+ "${D}/${TARGET_ARCH}/lib32 ${D}/${TARGET_ARCH}/lib64 ${D}/${TARGET_ARCH}/lib"

do_install[postfuncs] += "do_install_gcc_lafile_fixup"
do_install_gcc_lafile_fixup () {
    for lafile in ${D}/${TARGET_ARCH}/sysroot${target_libdir}/*.la ; do
        if "$lafile" != "${D}/${TARGET_ARCH}/sysroot${target_libdir}/*.la"; then
            sed -e "s:-L`readlink -f ${B}`/targets/${TARGET_ARCH}/[^ ']* *::" \
                -i $lafile
        fi
    done
}

# This is useful to provide valgrind with a non-stripped ld lib.
# Set USE_gcc_ld_so_unstripped = "1" and add valgrind to rootfs.
RECIPE_FLAGS += "gcc_ld_so_unstripped"
LD_SO_UNSTRIPPED_PRE:>USE_ldunstripped = "do_install_ld_so_unstripped_pre"
LD_SO_UNSTRIPPED_POST:>USE_ldunstripped = "do_install_ld_so_unstripped_post"
do_install[postfuncs] =+ "${LD_SO_UNSTRIPPED_PRE}"
do_install[postfuncs] += "${LD_SO_UNSTRIPPED_POST}"

do_install_ld_so_unstripped_pre(){
    cp ${D}/${TARGET_ARCH}/lib/ld-${TOOLCHAIN_LIBC_VERSION}.so ${S}/../.
}

do_install_ld_so_unstripped_post(){
    cp ${S}/../ld-${TOOLCHAIN_LIBC_VERSION}.so ${D}/${TARGET_ARCH}/lib/.
}
