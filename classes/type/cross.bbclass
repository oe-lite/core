# -*- mode:python; -*-

RECIPE_ARCH		= "${MACHINE_ARCH}"
RECIPE_ARCH_MACHINE	= "cross/${MACHINE}"

# Default packages is stage (cross) packages
PACKAGES		+= "${TARGET_PACKAGES}"
TARGET_PACKAGES		?= ""

#DEFAULT_DEPENDS = "cross:toolchain ${TARGET_ARCH}/sysroot-dev"

# Set host=build to get architecture triplet build/build/target
HOST_ARCH		= "${BUILD_ARCH}"
HOST_PREFIX		= "${BUILD_PREFIX}"
HOST_CFLAGS		= "${BUILD_CFLAGS}"
HOST_CPPFLAGS		= "${BUILD_CPPFLAGS}"
HOST_OPTIMIZATION	= "${BUILD_OPTIMIZATION}"
HOST_CFLAGS		= "${BUILD_CFLAGS}"
HOST_CXXFLAGS		= "${BUILD_CXXFLAGS}"
HOST_LDFLAGS		= "${BUILD_LDFLAGS}"

# Arch tuple arguments for configure (oe_runconf in autotools.bbclass)
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH} --host=${HOST_ARCH} --target=${TARGET_ARCH}"

# Use stage_* path variables for host paths
base_prefix		= "${stage_base_prefix}"
prefix			= "${stage_prefix}"
exec_prefix		= "${stage_exec_prefix}"
base_bindir		= "${stage_base_bindir}"
base_sbindir		= "${stage_base_sbindir}"
base_libexecdir		= "${stage_base_libexecdir}"
base_libdir		= "${stage_base_libdir}"
base_includedir		= "${stage_base_includedir}"
datadir			= "${stage_datadir}"
sysconfdir		= "${stage_sysconfdir}"
servicedir		= "${stage_servicedir}"
sharedstatedir		= "${stage_sharedstatedir}"
localstatedir		= "${stage_localstatedir}"
runitservicedir		= "${stage_runitservicedir}"
infodir			= "${stage_infodir}"
mandir			= "${stage_mandir}"
docdir			= "${stage_docdir}"
bindir			= "${stage_bindir}"
sbindir			= "${stage_sbindir}"
libexecdir		= "${stage_libexecdir}"
libdir			= "${stage_libdir}"
includedir		= "${stage_includedir}"

TARGET_PACKAGE_TYPE	= "machine"

# Fixup PACKAGE_TYPE_* variables for target packages
addhook fixup_package_type to post_recipe_parse first
def fixup_package_type(d):
    target_packages = (d.get("TARGET_PACKAGES") or "").split()
    target_package_type = d.get("TARGET_PACKAGE_TYPE")
    for pkg in target_packages:
        d.set("PACKAGE_TYPE_%s"%(pkg), target_package_type)

REBUILDALL_SKIP = "1"
RELAXED = "1"
