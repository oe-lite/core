# Cross packages are built indirectly via dependency, no need for them
# to be a direct target of 'world'
EXCLUDE_FROM_WORLD = "1"

PACKAGES = ""

BASE_PACKAGE_ARCH	= "${SDK_ARCH}"

# Set host=build
HOST_ARCH		= "${BUILD_ARCH}"
HOST_OS			= "${BUILD_OS}"
HOST_VENDOR		= "${BUILD_VENDOR}"
HOST_CC_ARCH		= "${BUILD_CC_ARCH}"
HOST_EXEEXT		= "${BUILD_EXEEXT}"

# and target=sdk to get architecture triplet build/build/sdk
TARGET_ARCH		= "${SDK_ARCH}"
TARGET_OS		= "${SDK_OS}"
TARGET_VENDOR		= "${SDK_VENDOR}"
TARGET_CC_ARCH		= "${SDK_CC_ARCH}"
TARGET_EXEEXT		= "${SDK_EXEEXT}"

# Use build compiler/linker flags
CPPFLAGS		= "${BUILD_CPPFLAGS}"
CFLAGS			= "${BUILD_CFLAGS}"
CXXFLAGS		= "${BUILD_CFLAGS}"
LDFLAGS			= "${BUILD_LDFLAGS}"

# Build and install to CROSS_DIR
base_prefix	= "${CROSS_DIR}${layout_base_prefix}"
prefix		= "${CROSS_DIR}${layout_prefix}"
exec_prefix	= "${CROSS_DIR}${layout_exec_prefix}"
base_bindir	= "${CROSS_DIR}${layout_base_bindir}"
base_sbindir	= "${CROSS_DIR}${layout_base_sbindir}"
base_libdir	= "${CROSS_DIR}${layout_base_libdir}"
sysconfdir	= "${CROSS_DIR}${layout_sysconfdir}"
localstatedir	= "${CROSS_DIR}${layout_localstatedir}"
servicedir	= "${CROSS_DIR}${layout_servicedir}"
sharedstatedir	= "${CROSS_DIR}${layout_sharedstatedir}"
datadir		= "${CROSS_DIR}${layout_datadir}"
infodir		= "${CROSS_DIR}${layout_infodir}"
mandir		= "${CROSS_DIR}${layout_mandir}"
docdir		= "${CROSS_DIR}${layout_docdir}"
bindir		= "${CROSS_DIR}${layout_bindir}"
sbindir		= "${CROSS_DIR}${layout_sbindir}"
libdir		= "${CROSS_DIR}${layout_libdir}"
libexecdir	= "${CROSS_DIR}${layout_libexecdir}"
includedir	= "${CROSS_DIR}${layout_includedir}"

#do_stage () {
#	oe_runmake install
#}

do_install () {
	:
}
