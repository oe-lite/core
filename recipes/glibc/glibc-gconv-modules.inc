# -*- mode:python; -*-

GCONV_MODULES_DIR = "${libdir}/gconv"

PACKAGES =+ "${GCONV_MODULES_PACKAGES} ${GCONV_MODULES_LIB_PACKAGES}"

META_EMIT_PREFIX += "package:GCONV_MODULES_ split:GCONV_MODULES_ packageqa:GCONV_MODULES_"

addhook auto_package_gconv_modules to post_recipe_parse before fixup_package_type before blacklist

def auto_package_gconv_modules(d):
    pn = d.get("PN")
    modules = (d.get("GCONV_MODULES") or "").split()
    module_dir = d.get("GCONV_MODULES_DIR")
    libs = (d.get("GCONV_LIBS") or "").split()

    packages = []
    for module in modules:
        pkg = "%s-gconv-module-%s"%(
            pn, module.lower().replace('_', '-'))
        devpkg = pkg + "-dev"
        d.set("FILES_" + pkg, "%s/%s.so"%(module_dir, module))
        packages.append(pkg)
        d.set("PROVIDES_" + pkg, "gconv-module-%s"%(
            module.lower().replace('_', '-')))
        d.set("DEPENDS_" + pkg, "%s-gconv-modules-config"%(pn,))
        d.set("RDEPENDS_" + pkg, "%s-gconv-modules-config"%(pn,))
    d.set("GCONV_MODULES_PACKAGES", " ".join(packages))

    lib_packages = []
    for lib in libs:
        pkg = "%s-gconv-%s"%(
            pn, lib.lower().replace('_', '-'))
        d.set("FILES_" + pkg, "%s/%s.so"%(module_dir, lib))
        lib_packages.append(pkg)
    d.set("GCONV_MODULES_LIB_PACKAGES", " ".join(lib_packages))

PACKAGES =+ "${PN}-gconv-modules"

PACKAGES =+ "${PN}-gconv-dbg ${PN}-gconv-modules-dbg"
FILES_${PN}-gconv-dbg = "${GCONV_MODULES_DIR}/.debug/lib*.so"
FILES_${PN}-gconv-modules-dbg = "${GCONV_MODULES_DIR}/.debug/*.so"

DEPENDS_${PN}-gconv-modules = "${GCONV_MODULES_PACKAGES}"
RDEPENDS_${PN}-gconv-modules = "${GCONV_MODULES_PACKAGES}"

# FIXME: Do we need a method for generating gconv-modules?  Perhaps create an
# image .oeclass for keeping selected modules and generate the gconv-modules.
PACKAGES =+ "${PN}-gconv-modules-config"
FILES_${PN}-gconv-modules-config = "${GCONV_MODULES_DIR}/gconv-modules"

CHRPATH_DIRS += "${libdir}/gconv"
FILES_${PN}-gconv-modules[qa] += "allow-elf-bins-in-other-dirs"
FILES_${PN}-gconv-modules[qa] += "allow-elf-libs-in-other-dirs"
PROVIDES_${PN}-gconv-modules[qa] += "allow-missing-provides"
DEPENDS_${PN}-gconv-modules[qa] += "allow-missing-lib-depends"
RDEPENDS_${PN}-gconv-modules[qa] += "allow-missing-lib-rdepends"
FILES_${PN}-util-getconf[qa] += "allow-elf-bins-in-other-dirs"
