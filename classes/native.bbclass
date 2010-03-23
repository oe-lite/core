#
RECIPE_ARCH			 = "native/${BUILD_ARCH}"
RECIPE_ARCH_MACHINE		 = "native/${BUILD_ARCH}--${MACHINE}"
#
PACKAGE_DIR_CROSS		= ""
PACKAGE_DIR_SYSROOT_ARCH	= "${PACKAGE_DIR_NATIVE_ARCH}"
PACKAGE_DIR_SYSROOT_MACHINE	= "${PACKAGE_DIR_NATIVE_MACHINE}"
#
TARGET_PACKAGE_OUTPUT_ARCH	= "${PACKAGE_DIR_NATIVE_ARCH}"
TARGET_PACKAGE_OUTPUT_MACHINE	= "${PACKAGE_DIR_NATIVE_MACHINE}"
#
STAGE_PACKAGE_OUTPUT_ARCH	= "${PACKAGE_DIR_NATIVE_ARCH}"
STAGE_PACKAGE_OUTPUT_MACHINE	= "${PACKAGE_DIR_NATIVE_MACHINE}"

STAGE_PACKAGE_PATH	 = "\
${STAGE_PACKAGE_DIR}/native/${BUILD_ARCH} \
${STAGE_PACKAGE_DIR}/native/${BUILD_ARCH}--${MACHINE} \
"

# Only stage packages
PACKAGES	= ""
RPROVIDES_${PN}	= ""

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

# but build for temporary install destination
#stage_base_prefix	= "${D}"

ORIG_DEPENDS := "${DEPENDS}"
DEPENDS_bbclassextend-native ?= "${ORIG_DEPENDS}"

python __anonymous () {
    if 'native' in (bb.data.getVar('BBCLASSEXTEND', d, True) or "").split():
        pn = bb.data.getVar("PN", d, True)
        depends = bb.data.getVar("DEPENDS_bbclassextend-native", d, True)
        deps = bb.utils.explode_deps(depends)
        suffixes = bb.data.getVar('SPECIAL_PKGSUFFIX', d, True).split()

        newdeps = []
        for dep in deps:
            if dep.endswith('-native'):
                newdeps.append(dep)
                continue
            for suffix in suffixes:
                if dep.endswith(suffix):
                    dep = dep.replace(suffix, '')
                    break
            newdeps.append(dep + '-native')
        bb.data.setVar('DEPENDS_bbclassextend-native', ' '.join(newdeps), d)

        sysroot_packages = bb.data.getVar('PACKAGES', d, True)
        stage_packages = bb.data.getVar('STAGE_PACKAGES', d, True)
        for package in set(sysroot_packages.split()).union(stage_packages.split()):
            provides = bb.data.getVar('PROVIDES_%s'%package, d, True) or ''
            for provide in provides.split():
                if provide.find(pn) != -1:
                    continue
                if not provide.endswith('-native'):
                    provides = provides.replace(provide, provide + '-native')
            bb.data.setVar('PROVIDES_%s'%package, provides, d)

        bb.data.setVar('OVERRIDES', bb.data.getVar('OVERRIDES', d, False) + ":bbclassextend-native", d)
}
