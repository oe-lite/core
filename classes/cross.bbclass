RECIPE_TYPE			 = "cross"
#
RECIPE_ARCH			 = "cross/${TARGET_ARCH}"
RECIPE_ARCH_MACHINE		 = ""

# Default packages is stage (cross) packages
SYSROOT_PACKAGES	?= ""
RPACKAGES		 = "${@cross_rpackages(d)}"
PACKAGES_append		+= "${RPACKAGES}"
RPROVIDES_${PN}		 = ""

# Set host=build to get architecture triplet build/build/target
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

# Arch tuple arguments for configure (oe_runconf in autotools.bbclass)
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH} --host=${HOST_ARCH} --target=${TARGET_ARCH}"

# Use the stage_* path variables
base_prefix		= "${stage_base_prefix}"
prefix			= "${stage_prefix}"
exec_prefix		= "${stage_exec_prefix}"
base_bindir		= "${stage_base_bindir}"
base_sbindir		= "${stage_base_sbindir}"
base_libdir		= "${stage_base_libdir}"
base_libexecdir		= "${stage_base_libexecdir}"
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

cross_do_install () {
    oe_runmake install
}

do_install () {
    cross_do_install
}

def cross_rpackages (d):
    packages = []
    for package in bb.data.getVar('SYSROOT_PACKAGES', d, True).split():
        packages += [package, package + '-sdk']
    return ' '.join(packages)


# Set PACKAGE_ARCH_* variables for runtime packages
python __anonymous () {
    for pkg in bb.data.getVar('RPACKAGES', d, True).split():
        pkg_arch = bb.data.getVar('PACKAGE_ARCH_%s'%pkg, d, True)
        if not pkg_arch:
            if pkg.endswith('-sdk'):
                sysroot = 'sdk'
            else:
                sysroot = 'machine'
            bb.data.setVar('PACKAGE_ARCH_%s'%pkg, '%s/${TARGET_ARCH}'%(sysroot), d)
}

FIXUP_RPROVIDES = cross_fixup_rprovides
def cross_fixup_rprovides(d):
    for package in bb.data.getVar('SYSROOT_PACKAGES', d, True).split():
    	rprovides = bb.data.getVar('RPROVIDES_%s'%(package), d, True)
	if rprovides:
            rprovides = rprovides.split()
        else:
            rprovides = []
        if not package in rprovides:
            rprovides = [package] + rprovides
            bb.data.setVar('RPROVIDES_%s'%(package), ' '.join(rprovides), d)
        sdkrprovides = []
        for rprovide in rprovides:
            if rprovide.startswith(package):
                rprovide = rprovide.replace(package, package + '-sdk', 1)
            sdkrprovides.append(rprovide)
        bb.data.setVar('RPROVIDES_%s-sdk'%(package), ' '.join(sdkrprovides), d)
