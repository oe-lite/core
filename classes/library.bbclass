# -*- mode:python; -*-
#
# inherit this for (single) library recipes
#

DEPENDS_${PN}		= "${PN}-dev_${PV}"
DEPENDS_${PN}-dev	= ""

FILES_${PN}	= "${base_libdir}/lib*${SOLIBS} ${libdir}/lib*${SOLIBS}"
FILES_${PN}-dev = "\
${base_libdir}/*${SOLIBSDEV} ${base_libdir}/*.a ${base_libdir}/*.la \
${libdir}/lib*${SOLIBSDEV} ${libdir}/*.a ${libdir}/*.la \
${base_libdir}/*.o  ${libdir}/*.o \
${libdir}/pkgconfig \
${includedir} \
${libdir}/*/include \
${datadir}/aclocal ${datadir}/pkgconfig \
${bindir}/*-config \
"
ALLOW_EMPTY_${PN}-dev = "0"

addhook library_depends to post_recipe_parse after fixup_package_type

def library_depends(d):
    pkg = d.get("PN")
    pkg_type = d.get("PACKAGE_TYPE_" + pkg) or d.get("RECIPE_TYPE")
    if pkg_type == "native":
        return
    pv = d.get("PV")
    devpkg = pkg + "-dev"
    pkg_depends = (d.get("DEPENDS_" + pkg) or "").split()

    pkg_rdepends = d.get("RDEPENDS_" + pkg)
    if pkg_rdepends is None:
        pkg_rdepends = []
        for dep in pkg_depends:
            item = oelite.item.OEliteItem(dep, (0, pkg_type))
            if item.type != pkg_type:
                continue
            if dep == (devpkg + "_" + pv):
                continue
            if item.name.startswith("lib"):
                pkg_rdepends.append(dep)
        if pkg_rdepends:
            d.set("RDEPENDS_" + pkg, " ".join(pkg_rdepends))
    else:
        pkg_rdepends = pkg_rdepends.split()

    devpkg_rdepends = (d.get("RDEPENDS_" + devpkg) or "").split()
    for dep in pkg_rdepends:
        item = oelite.item.OEliteItem(dep, (1, pkg_type))
        if item.name.startswith("lib") and not item.name.endswith("-dev"):
            if item.version:
                devdep = "%s:%s_%s"%(item.type, item.name + "-dev", item.type)
            else:
                devdep = "%s:%s"%(item.type, item.name + "-dev")
            devpkg_rdepends.append(dep + "-dev")
    d.set("RDEPENDS_" + devpkg, " ".join(devpkg_rdepends))
