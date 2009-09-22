BASE_PACKAGE_ARCH	 = "${SDK_SYS}-sdk-${TARGET_SYS}"

# Set host=sdk for architecture triplet build/sdk/target
HOST_ARCH		= "${SDK_ARCH}"
HOST_OS			= "${SDK_OS}"
HOST_VENDOR		= "${SDK_VENDOR}"
HOST_CC_ARCH		= "${SDK_CC_ARCH}"
HOST_EXEEXT		= "${SDK_EXEEXT}"

# Use sdk compiler/linker flags
CPPFLAGS		= "${SDK_CPPFLAGS}"
CFLAGS			= "${SDK_CFLAGS}"
CXXFLAGS		= "${SDK_CFLAGS}"
LDFLAGS			= "${SDK_LDFLAGS}"
