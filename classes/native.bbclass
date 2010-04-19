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

# and target=build for architecture triplet build/build/build
TARGET_ARCH		= "${BUILD_ARCH}"
TARGET_CPU		= "${BUILD_CPU}"
TARGET_OS		= "${BUILD_OS}"
TARGET_CPU_CROSS	= "${BUILD_CPU_CROSS}"
TARGET_CROSS		= "${BUILD_CROSS}"
TARGET_CC_ARCH		= "${BUILD_CC_ARCH}"
TARGET_EXEEXT		= "${BUILD_EXEEXT}"
TARGET_PREFIX		= "${BUILD_PREFIX}"

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

ORIG_DEPENDS := "${DEPENDS}"
DEPENDS_bbclassextend-native ?= "${ORIG_DEPENDS}"

python __anonymous () {
    if 'native' in (bb.data.getVar('BBCLASSEXTEND', d, True) or "").split():
        pn = bb.data.getVar("PN", d, True)
        depends = bb.data.getVar("DEPENDS_bbclassextend-native", d, True)
        suffixes = bb.data.getVar('SPECIAL_PKGSUFFIX', d, True)

        newdeps = []
        for dep in depends:
            if dep.endswith('-native'):
                newdeps.append(dep)
                continue
            for suffix in suffixes:
                if dep.endswith(suffix):
                    newdeps.append(dep.replace(suffix, '-native'))
                    continue
            newdeps.append(dep + '-native')
        bb.data.setVar('DEPENDS_bbclassextend-native', ' '.join(newdeps), d)
}

FIXUP_RPROVIDES = ''
