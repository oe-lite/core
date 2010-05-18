DEFAULT_CXX_DEPENDS = "${HOST_ARCH}-machine-libstdc++"
DEFAULT_CXX_DEPENDS_recipe-sdk = "${HOST_ARCH}-sdk-libstdc++"
DEFAULT_CXX_DEPENDS_recipe-canadian-cross = "${HOST_ARCH}-machine-libstdc++ ${TARGET_ARCH}-machine-libstdc++"
DEFAULT_CXX_DEPENDS_recipe-native = ""
DEFAULT_CXX_DEPENDS_recipe-cross = ""
DEFAULT_CXX_DEPENDS_recipe-sdk-cross = ""

DEFAULT_DEPENDS_append += "${DEFAULT_CXX_DEPENDS}"

SDK_CXXFLAGS_append	+= "-isystem ${SDK_SYSROOT}${sdk_includedir}/c++/${GCC_VERSION}/${SDK_ARCH} -isystem ${SDK_SYSROOT}${sdk_includedir}/c++/${GCC_VERSION}"
MACHINE_CXXFLAGS_append	+= "-isystem ${MACHINE_SYSROOT}${machine_includedir}/c++/${GCC_VERSION}/${MACHINE_ARCH} -isystem ${MACHINE_SYSROOT}${machine_includedir}/c++/${GCC_VERSION}"

export CXXFLAGS