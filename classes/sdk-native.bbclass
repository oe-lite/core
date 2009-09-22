# Native packages are built indirectly via dependency, no need for
# them to be a direct target of 'world'
EXCLUDE_FROM_WORLD = "1"

PACKAGES = ""

BASE_PACKAGE_ARCH = "${BUILD_ARCH}"

# Set host=sdk
HOST_ARCH		= "${SDK_ARCH}"
HOST_OS			= "${SDK_OS}"
HOST_VENDOR		= "${SDK_VENDOR}"
HOST_CC_ARCH		= "${SDK_CC_ARCH}"
HOST_EXEEXT		= "${SDK_EXEEXT}"

# and target=sdk for architecture triplet build/sdk/sdk
TARGET_ARCH		= "${SDK_ARCH}"
TARGET_OS		= "${SDK_OS}"
TARGET_VENDOR		= "${SDK_VENDOR}"
TARGET_CC_ARCH		= "${SDK_CC_ARCH}"
TARGET_EXEEXT		= "${SDK_EXEEXT}"

# Use sdk compiler/linker flags
CPPFLAGS		= "${SDK_CPPFLAGS}"
CFLAGS			= "${SDK_CFLAGS}"
CXXFLAGS		= "${SDK_CFLAGS}"
LDFLAGS			= "${SDK_LDFLAGS}"

# Build and install to STAGING_DIR_HOST
base_prefix	= "${STAGING_DIR_HOST}${layout_base_prefix}"
prefix		= "${STAGING_DIR_HOST}${layout_prefix}"
exec_prefix	= "${STAGING_DIR_HOST}${layout_exec_prefix}"
base_bindir	= "${STAGING_DIR_HOST}${layout_base_bindir}"
base_sbindir	= "${STAGING_DIR_HOST}${layout_base_sbindir}"
base_libdir	= "${STAGING_DIR_HOST}${layout_base_libdir}"
sysconfdir	= "${STAGING_DIR_HOST}${layout_sysconfdir}"
localstatedir	= "${STAGING_DIR_HOST}${layout_localstatedir}"
servicedir	= "${STAGING_DIR_HOST}${layout_servicedir}"
sharedstatedir	= "${STAGING_DIR_HOST}${layout_sharedstatedir}"
datadir		= "${STAGING_DIR_HOST}${layout_datadir}"
infodir		= "${STAGING_DIR_HOST}${layout_infodir}"
mandir		= "${STAGING_DIR_HOST}${layout_mandir}"
docdir		= "${STAGING_DIR_HOST}${layout_docdir}"
bindir		= "${STAGING_DIR_HOST}${layout_bindir}"
sbindir		= "${STAGING_DIR_HOST}${layout_sbindir}"
libdir		= "${STAGING_DIR_HOST}${layout_libdir}"
libexecdir	= "${STAGING_DIR_HOST}${layout_libexecdir}"
includedir	= "${STAGING_DIR_HOST}${layout_includedir}"

do_install () {
	:
}
