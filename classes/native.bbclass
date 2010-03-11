#
PACKAGE_DIR_CROSS		= ""
PACKAGE_DIR_SYSROOT_ARCH	= "${PACKAGE_DIR_NATIVE_ARCH}"
PACKAGE_DIR_SYSROOT_MACHINE	= "${PACKAGE_DIR_NATIVE_MACHINE}"
#
TARGET_PACKAGE_OUTPUT_ARCH	= "${PACKAGE_DIR_NATIVE_ARCH}"
TARGET_PACKAGE_OUTPUT_MACHINE	= "${PACKAGE_DIR_NATIVE_MACHINE}"
#
STAGE_PACKAGE_OUTPUT_ARCH	= "${PACKAGE_DIR_NATIVE_ARCH}"
STAGE_PACKAGE_OUTPUT_MACHINE	= "${PACKAGE_DIR_NATIVE_MACHINE}"
#
PACKAGE_ARCH_ARCH		 = "native/${BUILD_ARCH}"
PACKAGE_ARCH_MACHINE		 = "native/${BUILD_ARCH}--${MACHINE}"

# No default packages
PACKAGES = ""

# When this class has packaging enabled, setting RPROVIDES becomes unnecessary.
#RPROVIDES = "${PN}"

# Set host=build
HOST_ARCH		= "${BUILD_ARCH}"
HOST_CPU		= "${BUILD_CPU}"
HOST_OS			= "${BUILD_OS}"
HOST_CPU_CROSS		= "${BUILD_CPU_CROSS}"
HOST_CROSS		= "${BUILD_CROSS}"
HOST_CC_ARCH		= "${BUILD_CC_ARCH}"
HOST_EXEEXT		= "${BUILD_EXEEXT}"
HOST_PREFIX		= "${BUILD_PREFIX}"

# and target=build for architecture triplet build/build/build
TARGET_ARCH		= "${BUILD_ARCH}"
TARGET_CPU		= "${BUILD_CPU}"
TARGET_OS		= "${BUILD_OS}"
TARGET_CPU_CROSS	= "${BUILD_CPU_CROSS}"
TARGET_CROSS		= "${BUILD_CROSS}"
TARGET_CC_ARCH		= "${BUILD_CC_ARCH}"
TARGET_EXEEXT		= "${BUILD_EXEEXT}"
TARGET_PREFIX		= "${BUILD_PREFIX}"

# Use the stage_* path variables
base_prefix		= "${stage_base_prefix}"
prefix			= "${stage_prefix}"
exec_prefix		= "${stage_exec_prefix}"
base_bindir		= "${stage_base_bindir}"
base_sbindir		= "${stage_base_sbindir}"
base_libdir		= "${stage_base_libdir}"
datadir			= "${stage_datadir}"
sysconfdir		= "${stage_syscondir}"
servicedir		= "${stage_servicedir}"
sharedstatedir		= "${stage_sharedstatedir}"
localstatedir		= "${stage_localstatedir}"
infodir			= "${stage_infodir}"
mandir			= "${stage_mandir}"
docdir			= "${stage_docdir}"
bindir			= "${stage_bindir}"
sbindir			= "${stage_sbindir}"
libexecdir		= "${stage_libexecdir}"
libdir			= "${stage_libdir}"
includedir		= "${stage_includedir}"

do_install () {
	oe_runmake DESTDIR=${D} install
}

#PKG_CONFIG_PATH .= "${EXTRA_NATIVE_PKGCONFIG_PATH}"
#PKG_CONFIG_SYSROOT_DIR = ""
