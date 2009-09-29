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

# Adjust filesystem layout according to Crosstool-NG layout
sysroot_prefix		= "${STAGING_DIR_TARGET}/${TARGET_ARCH}/sys-root"
base_prefix		= "${sysroot_prefix}${layout_base_prefix}"
prefix			= "${sysroot_prefix}${layout_prefix}"
exec_prefix		= "${sysroot_prefix}${layout_exec_prefix}"
base_bindir		= "${sysroot_prefix}${layout_base_bindir}"
base_sbindir		= "${sysroot_prefix}${layout_base_sbindir}"
base_libdir		= "${sysroot_prefix}${layout_base_libdir}"
sysconfdir		= "${sysroot_prefix}${layout_sysconfdir}"
localstatedir		= "${sysroot_prefix}${layout_localstatedir}"
servicedir		= "${sysroot_prefix}${layout_servicedir}"
sharedstatedir		= "${sysroot_prefix}${layout_sharedstatedir}"
datadir			= "${sysroot_prefix}${layout_datadir}"
infodir			= "${sysroot_prefix}${layout_infodir}"
mandir			= "${sysroot_prefix}${layout_mandir}"
docdir			= "${sysroot_prefix}${layout_docdir}"
bindir			= "${sysroot_prefix}${layout_bindir}"
sbindir			= "${sysroot_prefix}${layout_sbindir}"
libdir			= "${sysroot_prefix}${layout_libdir}"
libexecdir		= "${sysroot_prefix}${layout_libexecdir}"
includedir		= "${sysroot_prefix}${layout_includedir}"

do_stage () {
	oe_runmake install
}

do_install () {
	:
}
