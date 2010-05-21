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
base_libexecdir		= "${stage_base_libexecdir}"
base_libdir		= "${stage_base_libdir}"
base_includedir		= "${stage_base_includedir}"
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

FIXUP_PACKAGE_ARCH = native_fixup_package_arch
def native_fixup_package_arch(d):
    arch = bb.data.getVar('RECIPE_ARCH', d, True).partition('native/')
    if not arch[0] and arch[1]:
        # take part after / of RECIPE_ARCH if it begins with $RECIPE_TYPE/
        arch = arch[2]
    else:
        arch = '${BUILD_ARCH}'
    for pkg in bb.data.getVar('PACKAGES', d, True).split():
        if not bb.data.getVar('PACKAGE_ARCH_'+pkg, d, False):
            pkg_arch = 'native/'+arch
            bb.data.setVar('PACKAGE_ARCH_'+pkg, pkg_arch, d)

FIXUP_PROVIDES = native_fixup_provides
def native_fixup_provides(d):
    target_arch = bb.data.getVar('TARGET_ARCH', d, True) + '/'
    pn = bb.data.getVar('PN', d, True)
    bpn = bb.data.getVar('BPN', d, True)
    for pkg in bb.data.getVar('PACKAGES', d, True).split():
    	provides = (bb.data.getVar('PROVIDES_'+pkg, d, True) or '').split()
        provides_changed = False
	if pkg == pn:
            cross_provides = target_arch + bpn
            if not cross_provides in provides:
                provides += [cross_provides]
                provides_changed = True
        if not pkg in provides:
            provides = [pkg] + provides
            provides_changed = True
        if provides_changed:
            bb.data.setVar('PROVIDES_'+pkg, ' '.join(provides), d)
	if bb.data.getVar('RPROVIDES_'+pkg, d, True):
            bb.data.setVar('RPROVIDES_'+pkg, '', d)
	if bb.data.getVar('RDEPENDS_'+pkg, d, True):
            bb.data.setVar('RDEPENDS_'+pkg, '', d)
