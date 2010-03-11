#
PACKAGE_DIR_CROSS		= ""
PACKAGE_DIR_SYSROOT_ARCH	= ""
PACKAGE_DIR_SYSROOT_MACHINE	= ""
#
TARGET_PACKAGE_OUTPUT_ARCH	= "${PACKAGE_DIR_SDK_ARCH}"
TARGET_PACKAGE_OUTPUT_MACHINE	= "${PACKAGE_DIR_SDK_MACHINE}"
#
STAGE_PACKAGE_OUTPUT_ARCH	= "${PACKAGE_DIR}/cross/${SDK_ARCH_ABI}"
STAGE_PACKAGE_OUTPUT_MACHINE	= ""
#
PACKAGE_ARCH_ARCH		 = "cross/${SDK_ARCH}"
PACKAGE_ARCH_MACHINE		 = "cross/${SDK_ARCH}--${MACHINE}"

# No default packages
PACKAGES = ""

# Set host=build
HOST_ARCH		= "${BUILD_ARCH}"
HOST_CPU		= "${BUILD_CPU}"
HOST_OS			= "${BUILD_OS}"
HOST_CPU_CROSS		= "${BUILD_CPU_CROSS}"
HOST_CROSS		= "${BUILD_CROSS}"
HOST_CC_ARCH		= "${BUILD_CC_ARCH}"
HOST_EXEEXT		= "${BUILD_EXEEXT}"
HOST_PREFIX		= "${BUILD_PREFIX}"

# and target=sdk to get architecture triplet build/build/sdk
TARGET_ARCH		= "${SDK_ARCH}"
TARGET_CPU		= "${SDK_CPU}"
TARGET_OS		= "${SDK_OS}"
TARGET_CPU_CROSS	= "${SDK_CPU_CROSS}"
TARGET_CROSS		= "${SDK_CROSS}"
TARGET_CC_ARCH		= "${SDK_CC_ARCH}"
TARGET_EXEEXT		= "${SDK_EXEEXT}"
TARGET_PREFIX		= "${SDK_PREFIX}"

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
