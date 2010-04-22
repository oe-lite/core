RECIPE_TYPE			 = "native"
#
RECIPE_ARCH			 = "native/${BUILD_ARCH}"
RECIPE_ARCH_MACHINE		 = "native/${BUILD_ARCH}--${MACHINE}"

# Native packages does not runtime provide anything
RPROVIDES_${PN}	= ""
RDEPENDS_${PN}-dev = ""

# Set host=build
HOST_ARCH		= "${BUILD_ARCH}"
HOST_CPU		= "${BUILD_CPU}"
HOST_OS			= "${BUILD_OS}"
HOST_CPU_CROSS		= "${BUILD_CPU_CROSS}"
HOST_CROSS		= "${BUILD_CROSS}"
HOST_CC_ARCH		= "${BUILD_CC_ARCH}"
HOST_EXEEXT		= "${BUILD_EXEEXT}"
HOST_PREFIX		= "${BUILD_PREFIX}"
HOST_CPPFLAGS		= "${BUILD_CPPFLAGS}"
HOST_CFLAGS		= "${BUILD_CFLAGS}"
HOST_CXXFLAGS		= "${BUILD_CXXFLAGS}"
HOST_LDFLAGS		= "${BUILD_LDFLAGS}"

# and target=build for architecture triplet build/build/build
TARGET_ARCH		= "${BUILD_ARCH}"
TARGET_CPU		= "${BUILD_CPU}"
TARGET_OS		= "${BUILD_OS}"
TARGET_CPU_CROSS	= "${BUILD_CPU_CROSS}"
TARGET_CROSS		= "${BUILD_CROSS}"
TARGET_CC_ARCH		= "${BUILD_CC_ARCH}"
TARGET_EXEEXT		= "${BUILD_EXEEXT}"
TARGET_PREFIX		= "${BUILD_PREFIX}"
TARGET_CPPFLAGS		= "${BUILD_CPPFLAGS}"
TARGET_CFLAGS		= "${BUILD_CFLAGS}"
TARGET_CXXFLAGS		= "${BUILD_CXXFLAGS}"
TARGET_LDFLAGS		= "${BUILD_LDFLAGS}"

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

base_do_install() {
    oe_runmake install
}

ORIG_DEPENDS := "${DEPENDS}"
DEPENDS_bbclassextend-native ?= "${ORIG_DEPENDS}"

python __anonymous () {
    if 'native' in (bb.data.getVar('BBCLASSEXTEND', d, True) or "").split():
        pn = bb.data.getVar("PN", d, True)
        depends = bb.utils.explode_deps(bb.data.getVar("DEPENDS_bbclassextend-native", d, True))
        suffixes = bb.data.getVar('SPECIAL_PKGSUFFIX', d, True).split()

        newdeps = []
        for dep in depends:
            if dep.endswith('-native'):
                newdeps.append(dep)
                continue
            for suffix in suffixes:
                if dep.endswith(suffix):
                    dep = dep.replace(suffix, '')
                    break
            newdeps.append(dep + '-native')
        bb.data.setVar('DEPENDS_bbclassextend-native', ' '.join(newdeps), d)

        packages = bb.data.getVar('PACKAGES', d, True)
        for package in packages.split():
            provides = bb.data.getVar('PROVIDES_%s'%package, d, True) or ''
            for provide in provides.split():
                if provide.find(pn) != -1:
                    continue
                if not provide.endswith('-native'):
                    provides = provides.replace(provide, provide + '-native')
            bb.data.setVar('PROVIDES_%s'%package, provides, d)

        bb.data.setVar('OVERRIDES', bb.data.getVar('OVERRIDES', d, False) + ":bbclassextend-native", d)
}

FIXUP_RPROVIDES = ''
