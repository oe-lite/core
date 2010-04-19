RECIPE_TYPE			 = "canadian-cross"
#
RECIPE_ARCH			 = "canadian/${SDK_ARCH}--${MACHINE_ARCH}"
RECIPE_ARCH_MACHINE		 = "canadian/${SDK_ARCH}--${MACHINE}"

# Set host=sdk for architecture triplet build/sdk/target
HOST_ARCH		= "${SDK_ARCH}"
HOST_CPU		= "${SDK_CPU}"
HOST_OS			= "${SDK_OS}"
HOST_CPU_CROSS		= "${SDK_CPU_CROSS}"
HOST_CROSS		= "${SDK_CROSS}"
HOST_CC_ARCH		= "${SDK_CC_ARCH}"
HOST_EXEEXT		= "${SDK_EXEEXT}"
HOST_PREFIX		= "${SDK_PREFIX}"
