#RECIPE_TYPES = "cross sdk-cross canadian-cross"
BBCLASSEXTEND = "cross sdk-cross canadian-cross"

# gcc and glibc versions should be locked down by distro
CT_CC_VERSION			 = "${GCC_VERSION}"
CT_LIBC_VERSION			 = "${GLIBC_VERSION}"

# the rest should be set here
MACHINE_CT_KERNEL_VERSION		?= "2.6.32.25"
SDK_CT_KERNEL_VERSION			?= "2.6.32.25"
BUILD_CT_KERNEL_VERSION			?= "2.6.32.25"
MACHINE_CT_LIBC_GLIBC_MIN_KERNEL	?= "2.6.32"
SDK_CT_LIBC_GLIBC_MIN_KERNEL		?= "2.6.0"
BUILD_CT_LIBC_GLIBC_MIN_KERNEL		?= "2.6.0"
CT_BINUTILS_VERSION			?= "2.20.1"
CT_GDB_VERSION				?= "7.2"
CT_GMP_VERSION				?= "5.0.1"
CT_MPFR_VERSION				?= "3.0.0"
CT_PPL_VERSION				?= "0.10.2"
CT_CLOOG_VERSION			?= "0.15.9"
CT_MPC_VERSION				?= "0.8.2"
CT_LIBELF_VERSION			?= "0.8.13"
CT_MINGWRT_VERSION			?= "3.18"
CT_W32API_VERSION			?= "3.14"

require toolchain.inc
