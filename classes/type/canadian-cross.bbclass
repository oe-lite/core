# -*- mode:python; -*-

RECIPE_ARCH		 = "${SDK_ARCH}--${MACHINE_ARCH}${MACHINE_OVERRIDE}"
MACHINE_OVERRIDE	?= ""

PACKAGES		+= "${HOST_PACKAGES} ${TARGET_PACKAGES}"
HOST_PACKAGES		?= ""
TARGET_PACKAGES		?= ""

# Get both sdk and machine cross toolchains and sysroots
#DEFAULT_DEPENDS += "${TARGET_ARCH}/toolchain ${TARGET_ARCH}/sysroot-dev"

# Set host=sdk for architecture triplet build/sdk/target
HOST_ARCH		= "${SDK_ARCH}"
HOST_CFLAGS		= "${SDK_CFLAGS}"
HOST_CPPFLAGS		= "${SDK_CPPFLAGS}"
HOST_OPTIMIZATION	= "${SDK_OPTIMIZATION}"
HOST_CFLAGS		= "${SDK_CFLAGS}"
HOST_CXXFLAGS		= "${SDK_CXXFLAGS}"
HOST_LDFLAGS		= "${SDK_LDFLAGS}"

HOST_TYPE		= "sdk"
TARGET_TYPE		= "machine"
HOST_CROSS		= "sdk-cross"
TARGET_CROSS		= "cross"

# Use sdk_* path variables for host paths
base_prefix		= "${sdk_base_prefix}"
prefix			= "${sdk_prefix}"
exec_prefix		= "${sdk_exec_prefix}"
base_bindir		= "${sdk_base_bindir}"
base_sbindir		= "${sdk_base_sbindir}"
base_libexecdir		= "${sdk_base_libexecdir}"
base_libdir		= "${sdk_base_libdir}"
base_includecdir	= "${sdk_base_includedir}"
datadir			= "${sdk_datadir}"
sysconfdir		= "${sdk_sysconfdir}"
servicedir		= "${sdk_servicedir}"
sharedstatedir		= "${sdk_sharedstatedir}"
localstatedir		= "${sdk_localstatedir}"
runitservicedir		= "${sdk_runitservicedir}"
infodir			= "${sdk_infodir}"
mandir			= "${sdk_mandir}"
docdir			= "${sdk_docdir}"
bindir			= "${sdk_bindir}"
sbindir			= "${sdk_sbindir}"
libexecdir		= "${sdk_libexecdir}"
libdir			= "${sdk_libdir}"
includedir		= "${sdk_includedir}"

# Fixup PACKAGE_TYPE_* variables for target packages
addhook fixup_package_type to post_recipe_parse first
def fixup_package_type(d):
    host_packages = (d.get("HOST_PACKAGES") or "").split()
    target_packages = (d.get("TARGET_PACKAGES") or "").split()
    for pkg in host_packages:
        d.set("PACKAGE_TYPE_%s"%(pkg), "sdk")
    for pkg in target_packages:
        d.set("PACKAGE_TYPE_%s"%(pkg), "machine")

REBUILDALL_SKIP = "1"
RELAXED = "1"
