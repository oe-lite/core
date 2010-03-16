#
RECIPE_ARCH			= "cross/${TARGET_CROSS}"
RECIPE_ARCH_MACHINE		= ""
#
PACKAGE_DIR_CROSS		= ""
PACKAGE_DIR_SYSROOT_ARCH	= ""
PACKAGE_DIR_SYSROOT_MACHINE	= ""
#
SYSROOT_PACKAGE_OUTPUT_ARCH	= "${PACKAGE_DIR_ARCH}"
SYSROOT_PACKAGE_OUTPUT_MACHINE	= "${PACKAGE_DIR_MACHINE}"

STAGE_PACKAGE_PATH	 = "\
${STAGE_PACKAGE_DIR}/machine/${MACHINE_CROSS} \
${STAGE_PACKAGE_DIR}/cross/${TARGET_CROSS} \
${STAGE_PACKAGE_DIR}/native/${BUILD_ARCH} \
"

# Default to only stage packages
PACKAGES	= ""
RPROVIDES_${PN}	= ""

# Set host=build to get architecture triplet build/build/target
HOST_ARCH		= "${BUILD_ARCH}"
HOST_CPU		= "${BUILD_CPU}"
HOST_OS			= "${BUILD_OS}"
HOST_CPU_CROSS		= "${BUILD_CPU_CROSS}"
HOST_CROSS		= "${BUILD_CROSS}"
HOST_CC_ARCH		= "${BUILD_CC_ARCH}"
HOST_EXEEXT		= "${BUILD_EXEEXT}"
HOST_PREFIX		= "${BUILD_PREFIX}"

# Use the stage_* path variables
base_prefix		= "${stage_base_prefix}"
prefix			= "${stage_prefix}"
exec_prefix		= "${stage_exec_prefix}"
base_bindir		= "${stage_base_bindir}"
base_sbindir		= "${stage_base_sbindir}"
base_libdir		= "${stage_base_libdir}"
datadir			= "${stage_datadir}"
sysconfdir		= "${stage_sysconfdir}"
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
	oe_runmake install
}
