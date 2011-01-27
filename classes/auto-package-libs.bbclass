PACKAGES =+ "${LIBS_AUTO_PACKAGES}"

AUTO_PACKAGE_LIBS ?= ""

AUTO_PACKAGE_FUNCS += "auto_package_libs"

def auto_package_libs (d):
    pn = d.getVar("PN", True)
    libs = (d.getVar("AUTO_PACKAGE_LIBS", False) or "").split()
    libsuffix = d.getVar("AUTO_PACKAGE_LIBS_LIBSUFFIX", True) or ""
    packages = []

    def get_extra_files(pkg):
        extra_files = d.getVar("EXTRA_FILES_" + pkg, False)
        if extra_files:
            return " " + extra_files
        return ""

    for lib in libs:
        pkg = "%s-lib%s"%(pn, lib.replace("_", "-").lower())
        devpkg = pkg + "-dev"
        packages += [ pkg, pkg + "-dev" ]

        pkg_libsuffix = d.getVar("LIBSUFFIX_%s"%(pkg), True) or libsuffix
        d.setVar("FILES_" + pkg,
                 "${libdir}/lib%s%s${SOLIBS} "%(lib, pkg_libsuffix) +
                 get_extra_files(pkg))

        pkg_libsuffix = d.getVar("LIBSUFFIX_%s"%(pkg), True) or pkg_libsuffix
        d.setVar("FILES_" + devpkg,
                 "${libdir}/lib%s%s${SOLIBSDEV} "%(lib, pkg_libsuffix) +
                 "${libdir}/lib%s%s.la "%(lib, pkg_libsuffix) +
                 "${libdir}/lib%s%s.a "%(lib, pkg_libsuffix) +
                 "${libdir}/pkgconfig/%s%s.pc "%(lib, pkg_libsuffix) +
                 get_extra_files(devpkg))

        d.setVar("RPROVIDES_" + pkg, "lib%s${RE} "%(lib))
        d.setVar("PROVIDES_" + devpkg, "lib%s${RE} "%(lib))
        d.setVar("PROVIDES_" + pkg, "lib%s${RE}_${PF}"%(lib))
        d.setVar("DEPENDS_" + devpkg, "lib%s${RE}_${PF}"%(lib))
    
    d.setVar("LIBS_AUTO_PACKAGES", " ".join(packages))
