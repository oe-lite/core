DEFAULT_CXX_DEPENDS = "${HOST_ARCH}/sysroot-libstdc++"
DEFAULT_CXX_DEPENDS_append_recipe-canadian-cross = " ${TARGET_ARCH}/sysroot-libstdc++"
DEFAULT_CXX_DEPENDS_recipe-native = ""

DEFAULT_DEPENDS_append += "${DEFAULT_CXX_DEPENDS}"

SDK_CXXFLAGS_append	+= "-isystem ${SDK_SYSROOT}${sdk_includedir}/c++/${GCC_VERSION}/${SDK_ARCH} -isystem ${SDK_SYSROOT}${sdk_includedir}/c++/${GCC_VERSION}"
MACHINE_CXXFLAGS_append	+= "-isystem ${MACHINE_SYSROOT}${machine_includedir}/c++/${GCC_VERSION}/${MACHINE_ARCH} -isystem ${MACHINE_SYSROOT}${machine_includedir}/c++/${GCC_VERSION}"

export CXX
export CXXFLAGS
export BUILD_CXX
export BUILD_CXXFLAGS
