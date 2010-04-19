RECIPE_TYPE			 = "sdk"
#
RECIPE_ARCH			 = "sdk/${SDK_ARCH}"
RECIPE_ARCH_MACHINE		 = "sdk/${SDK_ARCH}--${MACHINE}"

# Set host=sdk
HOST_ARCH		= "${SDK_ARCH}"
HOST_CPU		= "${SDK_CPU}"
HOST_OS			= "${SDK_OS}"
HOST_CPU_CROSS		= "${SDK_CPU_CROSS}"
HOST_CROSS		= "${SDK_CROSS}"
HOST_CC_ARCH		= "${SDK_CC_ARCH}"
HOST_EXEEXT		= "${SDK_EXEEXT}"
HOST_PREFIX		= "${SDK_PREFIX}"

# and target=sdk for architecture triplet build/sdk/sdk
TARGET_ARCH		= "${SDK_ARCH}"
TARGET_CPU		= "${SDK_CPU}"
TARGET_OS		= "${SDK_OS}"
TARGET_CPU_CROSS	= "${SDK_CPU_CROSS}"
TARGET_CROSS		= "${SDK_CROSS}"
TARGET_CC_ARCH		= "${SDK_CC_ARCH}"
TARGET_EXEEXT		= "${SDK_EXEEXT}"
TARGET_PREFIX		= "${SDK_PREFIX}"

do_install () {
	:
}
