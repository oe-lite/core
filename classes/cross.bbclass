RECIPE_TYPE		= "cross"
#
RECIPE_ARCH		= "cross/${TARGET_ARCH}"
RECIPE_ARCH_MACHINE	= ""

# No default build dependencies (for now)
DEFAULT_DEPENDS		= ""

# Default packages is stage (cross) packages
SYSROOT_PACKAGES	?= ""
MACHINE_SYSROOT_PACKAGES = "${@machine_sysroot_packages(d)}"
SDK_SYSROOT_PACKAGES     = "${@sdk_sysroot_packages(d)}"
RPACKAGES		 = "${MACHINE_SYSROOT_PACKAGES} ${SDK_SYSROOT_PACKAGES}"
PACKAGES_append		+= "${RPACKAGES}"
RPROVIDES_${PN}          = ""

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

# But let's get rid of the stupid /usr thingy
stage_prefix		= "${stage_base_prefix}"

cross_do_install () {
    oe_runmake install
}

do_install () {
    cross_do_install
}


def machine_sysroot_packages(d):
    packages = (bb.data.getVar('SYSROOT_PACKAGES', d, True) or '').split()
    def sysroot_to_machine(s):
        return s.replace('sysroot', 'machine')
    return ' '.join(map(sysroot_to_machine, packages))

def sdk_sysroot_packages(d):
    packages = (bb.data.getVar('SYSROOT_PACKAGES', d, True) or '').split()
    def sysroot_to_sdk(s):
        return s.replace('sysroot', 'sdk')
    return ' '.join(map(sysroot_to_sdk, packages))


# Set PACKAGE_ARCH_* variables for runtime packages
python __anonymous () {
    packages = bb.data.getVar('SYSROOT_PACKAGES', d, True).split()
    mach_packages = bb.data.getVar('MACHINE_SYSROOT_PACKAGES', d, True).split()
    sdk_packages = bb.data.getVar('SDK_SYSROOT_PACKAGES', d, True).split()
    for pkg in packages:
        mach_pkg = pkg.replace('sysroot', 'machine')
        if (mach_pkg in mach_packages
            and not bb.data.getVar('PACKAGE_ARCH_%s'%mach_pkg, d, False)):
            pkg_arch = bb.data.getVar('PACKAGE_ARCH_%s'%pkg, d, False)
            if pkg_arch:
                pkg_arch = pkg_arch.replace('sysroot/', 'machine/')
            else:
                pkg_arch = 'machine/${TARGET_ARCH}'
            bb.data.setVar('PACKAGE_ARCH_%s'%mach_pkg, pkg_arch, d)
        sdk_pkg = pkg.replace('sysroot', 'sdk')
        if (sdk_pkg in sdk_packages
            and not bb.data.getVar('PACKAGE_ARCH_%s'%sdk_pkg, d, False)):
            pkg_arch = bb.data.getVar('PACKAGE_ARCH_%s'%pkg, d, False)
            if pkg_arch:
                pkg_arch = pkg_arch.replace('sysroot/', 'sdk/')
            else:
                pkg_arch = 'sdk/${TARGET_ARCH}'
            bb.data.setVar('PACKAGE_ARCH_%s'%sdk_pkg, pkg_arch, d)
}


FIXUP_PROVIDES = cross_fixup_provides
def cross_fixup_provides(d):
    packages = bb.data.getVar('SYSROOT_PACKAGES', d, True).split()
    mach_packages = bb.data.getVar('MACHINE_SYSROOT_PACKAGES', d, True).split()
    sdk_packages = bb.data.getVar('SDK_SYSROOT_PACKAGES', d, True).split()

    for pkg in packages:
        provides = bb.data.getVar('PROVIDES_%s'%(pkg), d, True)
        rprovides = bb.data.getVar('RPROVIDES_%s'%(pkg), d, True)
        depends = bb.data.getVar('DEPENDS_%s'%(pkg), d, True)
        rdepends = bb.data.getVar('DEPENDS_%s'%(pkg), d, True)

        if provides:
            provides = provides.split()
        else:
            provides = []
        if not pkg in provides:
            provides = [pkg] + provides
        provides = ' '.join(provides)

        if rprovides:
            rprovides = rprovides.split()
        else:
            rprovides = []
        if not pkg in rprovides:
            rprovides = [pkg] + rprovides
        rprovides = ' '.join(rprovides)

        mach_pkg = pkg.replace('sysroot', 'machine')
        if mach_pkg in mach_packages:
            if not bb.data.getVar('PROVIDES_%s'%mach_pkg, d, False):
                mach_provides = provides.replace('sysroot', 'machine')
                bb.data.setVar('PROVIDES_%s'%mach_pkg, mach_provides, d)
            if not bb.data.getVar('RPROVIDES_%s'%mach_pkg, d, False):
                mach_rprovides = rprovides.replace('sysroot', 'machine')
                bb.data.setVar('RPROVIDES_%s'%mach_pkg, mach_rprovides, d)
            if depends and not bb.data.getVar('DEPENDS_%s'%mach_pkg, d, False):
                mach_depends = depends.replace('sysroot', 'machine')
                bb.data.setVar('DEPENDS_%s'%mach_pkg, mach_depends, d)
            if rdepends and not bb.data.getVar('RDEPENDS_%s'%mach_pkg, d, False):
                mach_rdepends = rdepends.replace('sysroot', 'machine')
                bb.data.setVar('RDEPENDS_%s'%mach_pkg, mach_rdepends, d)

        sdk_pkg = pkg.replace('sysroot', 'sdk')
        if sdk_pkg in sdk_packages:
            if not bb.data.getVar('PROVIDES_%s'%sdk_pkg, d, False):
                sdk_provides = provides.replace('sysroot', 'sdk')
                bb.data.setVar('PROVIDES_%s'%sdk_pkg, sdk_provides, d)
            if not bb.data.getVar('RPROVIDES_%s'%sdk_pkg, d, False):
                sdk_rprovides = rprovides.replace('sysroot', 'sdk')
                bb.data.setVar('RPROVIDES_%s'%sdk_pkg, sdk_rprovides, d)
            if depends and not bb.data.getVar('DEPENDS_%s'%sdk_pkg, d, False):
                sdk_depends = depends.replace('sysroot', 'sdk')
                bb.data.setVar('DEPENDS_%s'%sdk_pkg, sdk_depends, d)
            if rdepends and not bb.data.getVar('RDEPENDS_%s'%sdk_pkg, d, False):
                sdk_rdepends = rdepends.replace('sysroot', 'sdk')
                bb.data.setVar('RDEPENDS_%s'%sdk_pkg, sdk_rdepends, d)

PACKAGE_INSTALL_FUNCS_append += "package_install_sysroot_split"
