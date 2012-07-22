# -*- mode:python; -*-

CT_CC				= "gcc"
CT_CC_VERSION			= "${GCC_VERSION}"

CT_KERNEL			= "linux"
CT_KERNEL:TARGET_OS_mingw32	= "mingw32"
CT_KERNEL_VERSION		= "${MACHINE_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:sdk-cross	= "${SDK_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:sdk		= "${SDK_CT_KERNEL_VERSION}"
CT_KERNEL_VERSION:native	= "${BUILD_CT_KERNEL_VERSION}"
MACHINE_CT_KERNEL_VERSION	= "${USE_toolchain_kernel_version_machine}"
MACHINE_CT_KERNEL_VERSION:TARGET_OS_mingw32 = "${USE_toolchain_w32api_version}"
SDK_CT_KERNEL_VERSION		= "${USE_toolchain_kernel_version_sdk}"
SDK_CT_KERNEL_VERSION:TARGET_OS_mingw32 = "${USE_toolchain_w32api_version}"
BUILD_CT_KERNEL_VERSION		= "${USE_toolchain_kernel_version_build}"
RECIPE_FLAGS += "toolchain_kernel_version_machine toolchain_kernel_version_sdk \
	toolchain_kernel_version_build toolchain_w32api_version"

CT_LIBC_GLIBC_MIN_KERNEL_VERSION = "${USE_toolchain_min_kernel_machine}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:sdk-cross = "${USE_toolchain_min_kernel_sdk}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:sdk = "${USE_toolchain_min_kernel_sdk}"
CT_LIBC_GLIBC_MIN_KERNEL_VERSION:native	= "${USE_toolchain_min_kernel_build}"
RECIPE_FLAGS += "toolchain_min_kernel_machine \ toolchain_min_kernel_sdk \
	toolchain_min_kernel_build"


CT_LIBC				= "${USE_toolchain_libc}"
CT_LIBC:TARGET_OS_mingw32	= "mingw"
TOOLCHAIN_LIBC_VERSION = "${USE_toolchain_libc_version}"
TOOLCHAIN_LIBC_VERSION:sdk-cross = "2.12.2"
CT_LIBC_VERSION			= "${TOOLCHAIN_LIBC_VERSION}"
CT_LIBC_VERSION:TARGET_OS_mingw32 = "${USE_toolchain_mingwrt_version}"
# *sigh* why don't eglibc do real releases?
CT_EGLIBC_REVISION:USE_toolchain_libc_eglibc_revision = "${USE_toolchain_libc_eglibc_revision}"
RECIPE_FLAGS += "toolchain_libc \
	toolchain_libc_version toolchain_mingwrt_version \
	toolchain_libc_eglibc_revision"

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
