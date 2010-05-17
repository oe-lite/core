RECIPE_TYPE			 = "canadian-cross"
#
RECIPE_ARCH			 = "canadian/${SDK_ARCH}--${MACHINE_ARCH}"
RECIPE_ARCH_MACHINE		 = "canadian/${SDK_ARCH}--${MACHINE}"

# Get both sdk and machine cross toolchains and sysroots
DEFAULT_DEPENDS = "\
 ${HOST_ARCH}-toolchain ${HOST_ARCH}-sdk-dev\
 ${TARGET_ARCH}-toolchain ${TARGET_ARCH}-machine-dev\
"

# Set host=sdk for architecture triplet build/sdk/target
HOST_ARCH		= "${SDK_ARCH}"
HOST_CPUTYPE		= "${SDK_CPUTYPE}"
HOST_FPU		= "${SDK_FPU}"
HOST_CFLAGS		= "${SDK_CFLAGS}"
HOST_EXEEXT		= "${SDK_EXEEXT}"
HOST_PREFIX		= "${SDK_PREFIX}"
HOST_CPPFLAGS		= "${SDK_CPPFLAGS}"
HOST_OPTIMIZATION	= "${SDK_OPTIMIZATION}"
HOST_CFLAGS		= "${SDK_CFLAGS}"
HOST_CXXFLAGS		= "${SDK_CXXFLAGS}"
HOST_LDFLAGS		= "${SDK_LDFLAGS}"

# Arch tuple arguments for configure (oe_runconf in autotools.bbclass)
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH} --host=${HOST_ARCH} --target=${TARGET_ARCH}"
