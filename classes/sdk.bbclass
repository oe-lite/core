RECIPE_ARCH		 = "${SDK_ARCH}--${TARGET_ARCH}"

# Set host=sdk for architecture triplet build/sdk/target
HOST_ARCH		= "${SDK_ARCH}"
HOST_CPU		= "${SDK_CPU}"
HOST_VENDOR		= "${SDK_VENDOR}"
HOST_OS			= "${SDK_OS}"
HOST_CC_ARCH		= "${SDK_CC_ARCH}"
HOST_EXEEXT		= "${SDK_EXEEXT}"
HOST_PREFIX		= "${SDK_PREFIX}"

# Use sdk compiler/linker flags
CPPFLAGS		= "${SDK_CPPFLAGS}"
CFLAGS			= "${SDK_CFLAGS}"
CXXFLAGS		= "${SDK_CFLAGS}"
LDFLAGS			= "${SDK_LDFLAGS}"
