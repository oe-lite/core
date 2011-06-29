# -*- mode:python; -*-

inherit c

CXX_DEPENDS			= "host-cross:c++ host:libstdc++"
CXX_DEPENDS:>canadian-cross	= " target-cross:c++ target:libstdc++"
CLASS_DEPENDS += "${CXX_DEPENDS}"

SDK_CXXFLAGS_append	+= "-isystem ${SDK_SYSROOT}${sdk_includedir}/c++/${GCC_VERSION}/${SDK_ARCH} -isystem ${SDK_SYSROOT}${sdk_includedir}/c++/${GCC_VERSION}"
MACHINE_CXXFLAGS_append	+= "-isystem ${MACHINE_SYSROOT}${machine_includedir}/c++/${GCC_VERSION}/${MACHINE_ARCH} -isystem ${MACHINE_SYSROOT}${machine_includedir}/c++/${GCC_VERSION}"

export CXX
export CXXFLAGS
export BUILD_CXX
export BUILD_CXXFLAGS
