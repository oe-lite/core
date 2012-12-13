# -*- mode:python; -*-

CT_CC				= "gcc"
CT_CC_VERSION			= "${GCC_VERSION}"

CT_KERNEL			= "linux"
CT_KERNEL:TARGET_OS_mingw32	= "mingw32"
CT_KERNEL_VERSION		= "${MACHINE_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:sdk-cross	= "${SDK_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:sdk		= "${SDK_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:native	= "${BUILD_CT_KERNEL_VERSION}"
USE_KERNEL_VERSION_MACHINE = "toolchain_kernel_version_machine"
USE_KERNEL_VERSION_MACHINE:sdk-cross = ""
USE_KERNEL_VERSION_MACHINE:native = ""
USE_KERNEL_VERSION_MACHINE:sdk = ""
MACHINE_CT_KERNEL_VERSION	= "${USE_toolchain_kernel_version_machine}"
MACHINE_CT_KERNEL_VERSION:TARGET_OS_mingw32 = "${USE_toolchain_w32api_version}"
SDK_CT_KERNEL_VERSION		= "${USE_toolchain_kernel_version_sdk}"
SDK_CT_KERNEL_VERSION:TARGET_OS_mingw32 = "${USE_toolchain_w32api_version}"
BUILD_CT_KERNEL_VERSION		= "${USE_toolchain_kernel_version_build}"
RECIPE_FLAGS += " ${USE_KERNEL_VERSION_MACHINE} toolchain_kernel_version_sdk \
	toolchain_kernel_version_build toolchain_w32api_version"

CT_LIBC_GLIBC_MIN_KERNEL_VERSION = "${USE_toolchain_min_kernel_machine}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:sdk-cross = "${USE_toolchain_min_kernel_sdk}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:sdk = "${USE_toolchain_min_kernel_sdk}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:native	= "${USE_toolchain_min_kernel_build}"
RECIPE_FLAGS += "toolchain_min_kernel_machine \ toolchain_min_kernel_sdk \
	toolchain_min_kernel_build"

# Legacy (pre OE-lite/core 3.3) USE flags.
# These are considered deprecated, and will be removed in OE-lite/core 4.
RECIPE_FLAGS += "toolchain_libc \
	toolchain_libc_version toolchain_mingwrt_version \
	toolchain_libc_eglibc_revision"

#
# refactor libc/version USE flags:
#
# USE_machine_libc = "glibc:2.14"
# USE_machine_libc = "eglibc:2_16:HEAD"
# USE_machine_libc = "uclibc:0.9.33.2"
# USE_machine_libc = "mingw:3.18"
#
# USE_sdk_linux_libc = "glibc:2.12.2"
# USE_sdk_linux_libc = "eglibc:2_16:HEAD"
#
# USE_sdk_windows_libc = "mingw:3.18"
#

RECIPE_FLAGS += "machine_libc sdk_linux_libc sdk_windows_libc"

addhook libc_useflags to post_recipe_parse after set_useflags
def libc_useflags(d):
    recipe_type = d.get("RECIPE_TYPE")
    alt_libc = d.get("USE_toolchain_libc")
    alt_libc_version = d.get("USE_toolchain_libc_version")
    if recipe_type in ("cross", "canadian-cross", "machine"):
        libc_useflag = "USE_machine_libc"
    elif recipe_type in ("sdk-cross", "sdk"):
        sdk_os = d.get("SDK_OS")
        if sdk_os.startswith("linux"):
            libc_useflag = "USE_sdk_linux_libc"
            if recipe_type == "sdk-cross":
                alt_libc_version = "2.12.2"
        elif sdk_os.startswith("mingw"):
            libc_useflag = "USE_sdk_windows_libc"
            alt_libc = "mingw"
            alt_libc_version = d.get("USE_toolchain_mingwrt_version")
        else:
            return "ERROR: Unsupported SDK_OS %r"%(sdk_os)
    else:
        return "ERROR: Unsupported RECIPE_TYPE %r"%(recipe_type)
    libc_str = d.get(libc_useflag)
    if not libc_str:
        # Backwards compatibility with old USE flags
        libc_str = "%s:%s"%(alt_libc, alt_libc_version)
        if alt_libc == "eglibc":
            eglibc_revision = d.get("USE_toolchain_libc_eglibc_revision")
            if not eglibc_revision:
                return "ERROR: You must set USE_toolchain_libc_eglibc_revision"
            libc_str += ":" + eglibc_revision
    libc = libc_str.split(":")
    if libc[0] == "glibc":
        if len(libc) != 2:
            return "ERROR: Invalid %s flag: %r"%(libc_useflag, libc_str)
        d.set("CT_LIBC", "glibc")
        d.set("CT_LIBC_VERSION", libc[1])
    elif libc[0] == "eglibc":
        if len(libc) != 3:
            return "ERROR: Invalid %s flag: %r"%(libc_useflag, libc_str)
        d.set("CT_LIBC", "eglibc")
        d.set("CT_LIBC_VERSION", libc[1])
        d.set("CT_EGLIBC_REVISION", libc[2])
    elif libc[0] == "uclibc":
        if len(libc) != 2:
            return "ERROR: Invalid %s flag: %r"%(libc_useflag, libc_str)
        d.set("CT_LIBC", "uClibc")
        d.set("CT_LIBC_VERSION", libc[1])
    elif libc[0] == "mingw":
        if len(libc) != 2:
            return "ERROR: Invalid %s flag %r"%(libc_useflag, libc_str)
        d.set("CT_LIBC", "mingw")
        d.set("CT_LIBC_VERSION", libc[1])
    else:
        return "ERROR: Invalid %s flag %r"%(libc_useflag, libc_str)
    return True


CT_BINUTILS_VERSION	= "${USE_toolchain_binutils_version}"
RECIPE_FLAGS		+= "toolchain_binutils_version"

CT_GDB_VERSION		= "${USE_toolchain_gdb_version}"
RECIPE_FLAGS		+= "toolchain_gdb_version"

CT_GMP_VERSION		= "${USE_toolchain_gmp_version}"
RECIPE_FLAGS		+= "toolchain_gmp_version"

CT_MPFR_VERSION		= "${USE_toolchain_mpfr_version}"
RECIPE_FLAGS		+= "toolchain_mpfr_version"

CT_PPL_VERSION		= "${USE_toolchain_ppl_version}"
RECIPE_FLAGS		+= "toolchain_ppl_version"

CT_CLOOG_VERSION	= "${USE_toolchain_cloog_version}"
RECIPE_FLAGS		+= "toolchain_cloog_version"

CT_MPC_VERSION		= "${USE_toolchain_mpc_version}"
RECIPE_FLAGS		+= "toolchain_mpc_version"

CT_LIBELF_VERSION	= "${USE_toolchain_libelf_version}"
RECIPE_FLAGS		+= "toolchain_libelf_version"

CT_LTRACE_VERSION	= "${USE_toolchain_ltrace_version}"
RECIPE_FLAGS		+= "toolchain_ltrace_version"

CT_STRACE_VERSION	= "${USE_toolchain_strace_version}"
RECIPE_FLAGS		+= "toolchain_strace_version"

CT_MINGW_PDCURSES_VERSION = "${USE_toolchain_pdcurses_version}"
RECIPE_FLAGS		+= "toolchain_pdcurses_version"

CT_DMALLOC_VERSION	= "${USE_toolchain_dmalloc_version}"
RECIPE_FLAGS		+= "toolchain_dmalloc_version"
