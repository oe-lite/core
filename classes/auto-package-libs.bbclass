PACKAGES =+ "${LIBS_AUTO_PACKAGES}"

AUTO_PACKAGE_LIBS ?= ""
AUTO_PACKAGE_LIBS_LIBDIR ?= "${libdir}"
AUTO_PACKAGE_LIBS_PKGPREFIX ?= "lib"
AUTO_PACKAGE_LIBS_PROVIDEPREFIX ?= "lib"
AUTO_PACKAGE_LIBS_DEV_DEPENDS ?= ""
AUTO_PACKAGE_LIBS_DEV_RDEPENDS ?= "${AUTO_PACKAGE_LIBS_DEV_DEPENDS}"

addhook auto_package_libs to post_recipe_parse after base_after_parse before base_detect_machine_override fixup_package_arch fixup_provides

def auto_package_libs (d):
    pn = d.getVar("PN", True)
    libs = (d.getVar("AUTO_PACKAGE_LIBS", True) or "").split()
    libdirs = (d.getVar("AUTO_PACKAGE_LIBS_LIBDIR", True) or "").split()
    pkgprefix = d.getVar("AUTO_PACKAGE_LIBS_PKGPREFIX", True) or ""
    provideprefix = d.getVar("AUTO_PACKAGE_LIBS_PROVIDEPREFIX", True) or ""
    packages = []
    dev_depends = d.getVar("AUTO_PACKAGE_LIBS_DEV_DEPENDS", True) or ""
    dev_rdepends = d.getVar("AUTO_PACKAGE_LIBS_DEV_RDEPENDS", True) or ""

    def get_extra_files(pkg):
        return (d.getVar("EXTRA_FILES_" + pkg, True) or "").split()

    def split_libdir(libdir):
        libdir = libdir.split(":")
        if len(libdir) > 5:
            bb.fatal("invalid libdir in AUTO_PACKAGE_LIBS_LIBDIR: %s"%(libdir))
        if len(libdir) < 2:
            libdir.append("lib")
        if len(libdir) < 3:
            libdir.append("")
        if len(libdir) < 4:
	    libdir.append("${SOLIBS}")
        if len(libdir) < 5:
    	    libdir.append("${SOLIBSDEV}")

        return libdir

    for lib in libs:
        pkg = "%s-%s%s"%(pn, pkgprefix, lib.replace("_", "-").lower())
        devpkg = pkg + "-dev"
        packages += [ pkg, devpkg ]

        files = []
        pkg_libsuffix = d.getVar("LIBSUFFIX_%s"%(pkg), True)
        for libdir in libdirs:
            (libdir, libprefix, libsuffix, solibs, solibsdev) = split_libdir(libdir)
            if pkg_libsuffix is not None:
                libsuffix = pkg_libsuffix
            libname = "%s%s%s"%(libprefix, lib, libsuffix)
            files.append("%s/%s%s"%(libdir, libname, solibs))
        files += get_extra_files(pkg)
        d.setVar("FILES_" + pkg, " ".join(files))

        files = []
        pkg_libsuffix = d.getVar("LIBSUFFIX_%s"%(pkg), True)
        for libdir in libdirs:
            (libdir, libprefix, libsuffix, solibs, solibsdev) = split_libdir(libdir)
            if pkg_libsuffix is not None:
                libsuffix = pkg_libsuffix
            libname = "%s%s%s"%(libprefix, lib, libsuffix)
            files.append("%s/%s%s"%(libdir, libname, solibsdev))
            files.append("%s/%s.la"%(libdir, libname))
            files.append("%s/%s.a"%(libdir, libname))
            if pkg_libsuffix is None:
                pcfile = "${libdir}/pkgconfig/%s%s.pc"%(lib, libsuffix)
                if not pcfile in files:
                    files.append(pcfile)
        if pkg_libsuffix is not None:
            pcfile = "${libdir}/pkgconfig/%s%s.pc"%(lib, pkg_libsuffix)
            if not pcfile in files:
                files.append(pcfile)
        files += get_extra_files(devpkg)
        d.setVar("FILES_" + devpkg, " ".join(files))

        pkg_provides = (d.getVar("PROVIDES_" + pkg, True) or "").split()
        pkg_provides.append("%s%s${RE}_${PF}"%(provideprefix, lib))
        d.setVar("PROVIDES_" + pkg, " ".join(pkg_provides))

        devpkg_provides = (d.getVar("PROVIDES_" + devpkg, True) or "").split()
        devpkg_provides.append("%s%s${RE}"%(provideprefix, lib))
        d.setVar("PROVIDES_" + devpkg, " ".join(devpkg_provides))

        devpkg_depends = (d.getVar("DEPENDS_" + devpkg, True) or "").split()
        devpkg_depends.append("%s%s${RE}_${PF}"%(provideprefix, lib))
        devpkg_depends += dev_depends.split()
        d.setVar("DEPENDS_" + devpkg, " ".join(devpkg_depends))

        pkg_rprovides = (d.getVar("RPROVIDES_" + pkg, True) or "").split()
        pkg_rprovides.append("%s%s${RE}_${PF}"%(provideprefix, lib))
        pkg_rprovides.append("%s%s${RE}"%(provideprefix, lib))
        d.setVar("RPROVIDES_" + pkg, " ".join(pkg_rprovides))

        devpkg_rprovides = (d.getVar("RPROVIDES_" + devpkg, True) or "").split()
        devpkg_rprovides.append("%s%s${RE}-dev"%(provideprefix, lib))
        d.setVar("RPROVIDES_" + devpkg, " ".join(devpkg_rprovides))

        devpkg_rdepends = d.getVar("RDEPENDS_" + devpkg, True)
        if devpkg_rdepends is None:
            pkg_rdepends = (d.getVar("RDEPENDS_" + pkg, True) or "").split()
            devpkg_rdepends = []
            for dep in pkg_rdepends:
                if dep.endswith("-dev"):
                    devpkg_rdepends.append(dep)
                else:
                    devpkg_rdepends.append(dep + "-dev")
        else:
            devpkg_rdepends = devpkg_rdepends.split()
        devpkg_rdepends.append("%s%s${RE}_${PF}"%(provideprefix, lib))
        devpkg_rdepends += dev_rdepends.split()
        d.setVar("RDEPENDS_" + devpkg, " ".join(devpkg_rdepends))

    d.setVar("LIBS_AUTO_PACKAGES", " ".join(packages))
