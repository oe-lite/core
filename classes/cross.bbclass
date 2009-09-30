# Cross packages are built indirectly via dependency, no need for them
# to be a direct target of 'world'
EXCLUDE_FROM_WORLD = "1"

# No default packages
PACKAGES = ""

# Set host=build to get architecture triplet build/build/target
HOST_ARCH		= "${BUILD_ARCH}"
HOST_CPU		= "${BUILD_CPU}"
HOST_VENDOR		= "${BUILD_VENDOR}"
HOST_OS			= "${BUILD_OS}"
HOST_CC_ARCH		= "${BUILD_CC_ARCH}"
HOST_EXEEXT		= "${BUILD_EXEEXT}"
HOST_PREFIX		= "${BUILD_PREFIX}"

# Use build compiler/linker flags
CPPFLAGS		= "${BUILD_CPPFLAGS}"
CFLAGS			= "${BUILD_CFLAGS}"
CXXFLAGS		= "${BUILD_CFLAGS}"
LDFLAGS			= "${BUILD_LDFLAGS}"

# Staging area is sys-root dir of target cross compiler
base_prefix		= "${STAGING_DIR_TARGET}${layout_base_prefix}"
prefix			= "${STAGING_DIR_TARGET}${layout_prefix}"
exec_prefix		= "${STAGING_DIR_TARGET}${layout_exec_prefix}"
base_bindir		= "${STAGING_DIR_TARGET}${layout_base_bindir}"
base_sbindir		= "${STAGING_DIR_TARGET}${layout_base_sbindir}"
base_libdir		= "${STAGING_DIR_TARGET}${layout_base_libdir}"
sysconfdir		= "${STAGING_DIR_TARGET}${layout_sysconfdir}"
localstatedir		= "${STAGING_DIR_TARGET}${layout_localstatedir}"
servicedir		= "${STAGING_DIR_TARGET}${layout_servicedir}"
sharedstatedir		= "${STAGING_DIR_TARGET}${layout_sharedstatedir}"
datadir			= "${STAGING_DIR_TARGET}${layout_datadir}"
infodir			= "${STAGING_DIR_TARGET}${layout_infodir}"
mandir			= "${STAGING_DIR_TARGET}${layout_mandir}"
docdir			= "${STAGING_DIR_TARGET}${layout_docdir}"
bindir			= "${STAGING_DIR_TARGET}${layout_bindir}"
sbindir			= "${STAGING_DIR_TARGET}${layout_sbindir}"
libdir			= "${STAGING_DIR_TARGET}${layout_libdir}"
libexecdir		= "${STAGING_DIR_TARGET}${layout_libexecdir}"
includedir		= "${STAGING_DIR_TARGET}${layout_includedir}"

do_stage () {
	oe_runmake install
}

do_install () {
	:
}
