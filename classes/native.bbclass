# Native packages are built indirectly via dependency, no need for
# them to be a direct target of 'world'
EXCLUDE_FROM_WORLD = "1"

PACKAGES = ""

# When this class has packaging enabled, setting RPROVIDES becomes unnecessary.
#RPROVIDES = "${PN}"

BASE_PACKAGE_ARCH = "${BUILD_ARCH}"

# Set host=build
HOST_ARCH	= "${BUILD_ARCH}"
HOST_OS		= "${BUILD_OS}"
HOST_VENDOR	= "${BUILD_VENDOR}"
HOST_CC_ARCH	= "${BUILD_CC_ARCH}"
HOST_EXEEXT	= "${BUILD_EXEEXT}"
# and target=build for architecture triplet build/build/build
TARGET_ARCH	= "${BUILD_ARCH}"
TARGET_OS	= "${BUILD_OS}"
TARGET_VENDOR	= "${BUILD_VENDOR}"
TARGET_CC_ARCH	= "${BUILD_CC_ARCH}"
TARGET_EXEEXT	= "${BUILD_EXEEXT}"

# Use build compiler/linker flags
CPPFLAGS	= "${BUILD_CPPFLAGS}"
CFLAGS		= "${BUILD_CFLAGS}"
CXXFLAGS	= "${BUILD_CFLAGS}"
LDFLAGS		= "${BUILD_LDFLAGS}"

STAGING_BINDIR_CROSS = "${STAGING_DIR_BUILD}${layout_bindir}"

# Don't use site files for native builds
export CONFIG_SITE = ""

# Build and install to STAGING_DIR_BUILD
base_prefix	= "${STAGING_DIR_BUILD}${layout_base_prefix}"
prefix		= "${STAGING_DIR_BUILD}${layout_prefix}"
exec_prefix	= "${STAGING_DIR_BUILD}${layout_exec_prefix}"
base_bindir	= "${STAGING_DIR_BUILD}${layout_base_bindir}"
base_sbindir	= "${STAGING_DIR_BUILD}${layout_base_sbindir}"
base_libdir	= "${STAGING_DIR_BUILD}${layout_base_libdir}"
sysconfdir	= "${STAGING_DIR_BUILD}${layout_sysconfdir}"
localstatedir	= "${STAGING_DIR_BUILD}${layout_localstatedir}"
servicedir	= "${STAGING_DIR_BUILD}${layout_servicedir}"
sharedstatedir	= "${STAGING_DIR_BUILD}${layout_sharedstatedir}"
datadir		= "${STAGING_DIR_BUILD}${layout_datadir}"
infodir		= "${STAGING_DIR_BUILD}${layout_infodir}"
mandir		= "${STAGING_DIR_BUILD}${layout_mandir}"
docdir		= "${STAGING_DIR_BUILD}${layout_docdir}"
bindir		= "${STAGING_DIR_BUILD}${layout_bindir}"
sbindir		= "${STAGING_DIR_BUILD}${layout_sbindir}"
libdir		= "${STAGING_DIR_BUILD}${layout_libdir}"
libexecdir	= "${STAGING_DIR_BUILD}${layout_libexecdir}"
includedir	= "${STAGING_DIR_BUILD}${layout_includedir}"

do_stage () {
	if [ "${AUTOTOOLS_NATIVE_STAGE_INSTALL}" != "1" ]
	then
		oe_runmake install
	else
		autotools_stage_all
	fi
}

do_install () {
	true
}

#PKG_CONFIG_PATH .= "${EXTRA_NATIVE_PKGCONFIG_PATH}"
#PKG_CONFIG_SYSROOT_DIR = ""
