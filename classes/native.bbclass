RECIPE_TYPE			 = "native"
#
RECIPE_ARCH			 = "native/${BUILD_ARCH}"
RECIPE_ARCH_MACHINE		 = "native/${BUILD_ARCH}--${MACHINE}"

# Native packages does not runtime provide anything
RPACKAGES		= ""
RPROVIDES_${PN}		= ""
RDEPENDS_${PN}-dev 	= ""

# No default build dependencies (for now)
DEFAULT_DEPENDS		= ""

# Set host=build
HOST_ARCH		= "${BUILD_ARCH}"
HOST_CPUTYPE		= "${BUILD_CPUTYPE}"
HOST_FPU		= "${BUILD_FPU}"
HOST_CFLAGS		= "${BUILD_CFLAGS}"
HOST_EXEEXT		= "${BUILD_EXEEXT}"
HOST_PREFIX		= "${BUILD_PREFIX}"
HOST_CPPFLAGS		= "${BUILD_CPPFLAGS}"
HOST_OPTIMIZATION	= "${BUILD_OPTIMIZATION}"
HOST_CFLAGS		= "${BUILD_CFLAGS}"
HOST_CXXFLAGS		= "${BUILD_CXXFLAGS}"
HOST_LDFLAGS		= "${BUILD_LDFLAGS}"

# and target=build for architecture triplet build/build/build
TARGET_ARCH		= "${BUILD_ARCH}"
TARGET_CPUTYPE		= "${BUILD_CPUTYPE}"
TARGET_FPU		= "${BUILD_FPU}"
TARGET_CFLAGS		= "${BUILD_CFLAGS}"
TARGET_EXEEXT		= "${BUILD_EXEEXT}"
TARGET_PREFIX		= "${BUILD_PREFIX}"
TARGET_CPPFLAGS		= "${BUILD_CPPFLAGS}"
TARGET_OPTIMIZATION	= "${BUILD_OPTIMIZATION}"
TARGET_CFLAGS		= "${BUILD_CFLAGS}"
TARGET_CXXFLAGS		= "${BUILD_CXXFLAGS}"
TARGET_LDFLAGS		= "${BUILD_LDFLAGS}"

# Arch tuple arguments for configure (oe_runconf in autotools.bbclass)
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH}"

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
includedir		= "${stage_base_includedir}"

base_do_install() {
    oe_runmake install
}

FIXUP_PROVIDES = ''
