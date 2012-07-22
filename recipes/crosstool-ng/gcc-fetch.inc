# -*- mode:python; -*-

require conf/fetch/gnu.conf
require conf/fetch/kernelorg.conf
require conf/fetch/debian.conf
require conf/fetch/mpfr.conf
require conf/fetch/sourceforge.conf

SRC_URI += "${SRC_URI_GCC}"
SRC_URI_GCC ?= "${GNU_MIRROR}/gcc/gcc-${CT_CC_VERSION}/gcc-${CT_CC_VERSION}.tar.bz2;unpack=0"

SRC_URI += "${SRC_URI_BINUTILS}"
SRC_URI_BINUTILS = "${GNU_MIRROR}/binutils/binutils-${CT_BINUTILS_VERSION}.tar.bz2;unpack=0"

SRC_URI_GLIBC = "${GNU_MIRROR}/glibc/glibc-${CT_LIBC_VERSION}.tar.bz2;unpack=0 \
	git://sourceware.org/git/glibc-ports.git;tag=glibc-${CT_LIBC_VERSION}"
SRC_URI_GLIBC:TARGET_OS_mingw32 = ""

addhook set_kernel_subdir to post_recipe_parse after set_useflags before fetch_init
def set_kernel_subdir(d):
    if d.get("CT_KERNEL_VERSION") == "custom":
        return

    version = tuple(map(int, d.get("CT_KERNEL_VERSION").split(".")))
    if version[0] < 3:
        subdir = "v%d.%d"%(version[0], version[1])
        if ((version[:3] == (2,6,27) and version[3] >= 58) or
            (version[:3] == (2,6,32) and version[3] >= 28) or
            (version[:3] == (2,6,33) and version[3] >= 8) or
            (version[:3] == (2,6,34) and version[3] >= 8) or
            (version[:3] == (2,6,35) and version[3] >= 10)):
            subdir += "/longterm/v%d.%d.%d"%version[:3]
    else:
        subdir = "v%d.x"%(version[0])
    d.set("KERNEL_SUBDIR", subdir)

KERNEL_SUBDIR ??= ""
SRC_URI_LINUX = "${KERNELORG_MIRROR}/linux/kernel/${KERNEL_SUBDIR}/linux-${CT_KERNEL_VERSION}.tar.bz2;unpack=0"
SRC_URI_LINUX:TARGET_OS_mingw32 = ""

SRC_URI_GDB ?= "${GNU_MIRROR}/gdb/gdb-${CT_GDB_VERSION}.tar.bz2;unpack=0"

SRC_URI_LIBELF = "http://www.mr511.de/software/libelf-${CT_LIBELF_VERSION}.tar.gz;unpack=0"

SRC_URI_GMP = "${GNU_MIRROR}/gmp/gmp-${CT_GMP_VERSION}.tar.bz2;unpack=0"

SRC_URI_MPFR = "${MPFR_MIRROR}/mpfr-${CT_MPFR_VERSION}/mpfr-${CT_MPFR_VERSION}.tar.bz2;unpack=0"

SRC_URI_MPC = "http://www.multiprecision.org/mpc/download/mpc-${CT_MPC_VERSION}.tar.gz;unpack=0"

SRC_URI_STRACE = "${SOURCEFORGE_MIRROR}/project/strace/strace/${CT_STRACE_VERSION}/strace-${CT_STRACE_VERSION}.tar.bz2;unpack=0"

SRC_URI_LTRACE = "${DEBIAN_MIRROR}/main/l/ltrace/ltrace_${CT_LTRACE_VERSION}.orig.tar.gz;unpack=0"

SRC_URI_PDCURSES = "${SOURCEFORGE_MIRROR}/pdcurses/PDCurses-${CT_MINGW_PDCURSES_VERSION}.tar.gz;unpack=0"

SRC_URI:>TARGET_OS_mingw32 += " \
  ${SOURCEFORGE_MIRROR}/mingw/w32api-${CT_KERNEL_VERSION}-mingw32-src.tar.gz;unpack=0 \
  ${SOURCEFORGE_MIRROR}/mingw/mingwrt-${CT_LIBC_VERSION}-mingw32-src.tar.gz;unpack=0 \
"

do_unpack[postfuncs] += "do_unpack_ltrace_symlink"
do_unpack_ltrace_symlink () {
	if [ -n "${SRC_URI_LTRACE}" ] ; then
		ln -s ltrace_${CT_LTRACE_VERSION}.orig.tar.gz \
			${SRCDIR}/ltrace-${CT_LTRACE_VERSION}.tar.gz
        fi
	if [ -n "${SRC_URI_GLIBC}" ] ; then
		ln -s glibc-ports \
			${SRCDIR}/glibc-ports-${CT_LIBC_VERSION}
        fi
}

addhook gcc_set_src_uri to post_recipe_parse first before fetch_init after set_useflags gcc_select_gdb
def gcc_set_src_uri(d):
    def add_src(uri, flag=None):
        if flag is not None:
            if d.get(flag) == "1":
                return
        d.append("SRC_URI", "${%s}"%(uri), " ")
        if flag is not None:
            d.set(flag, "1")
    target_is_mingw = d.get("TARGET_OS") == "mingw32"
    target_is_linux = not target_is_mingw
    if d.get("CT_KERNEL_VERSION") != "custom" and target_is_linux:
        add_src("SRC_URI_LINUX")
    if d.get("CT_LIBC") == "glibc":
        add_src("SRC_URI_GLIBC")
    gcc_version = d.get("GCC_VERSION")
    if gcc_version.startswith("linaro-"):
        gcc_version = gcc_version[len("linaro-"):]
    v = map(int, gcc_version.split("-")[0].split("."))
    if v[0] == 4:
        if v[1] >= 3:
            add_src("SRC_URI_GMP", "CT_USE_GMP")
            add_src("SRC_URI_MPFR", "CT_USE_MPFR")
        if v[1] >= 5:
            add_src("SRC_URI_MPC", "CT_USE_MPC")
            if target_is_linux:
                add_src("SRC_URI_LIBELF", "CT_USE_LIBELF")
    if d.get("CT_DEBUG_gdb"):
        add_src("SRC_URI_GDB")
    if d.get("CT_DEBUG_ltrace"):
        add_src("SRC_URI_LTRACE")
        add_src("SRC_URI_LIBELF", "CT_USE_LIBELF")
    if d.get("CT_DEBUG_strace"):
        add_src("SRC_URI_STRACE")
    if target_is_mingw:
        add_src("SRC_URI_PDCURSES", "CT_USE_PDCURSES")
    # FIXME: add support for adding cloog and ppl


# could be nice to have a do_srcuriqa that tricks ct-ng into telling
# what to download, and then verify that this is identical to
# ${SRC_URI}
