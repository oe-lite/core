PACKAGES =+ "${LIBS_AUTO_PACKAGES}"

AUTO_PACKAGE_LIBS ?= ""
AUTO_PACKAGE_LIBS_LIBDIR ?= "${libdir}"
AUTO_PACKAGE_LIBS_PKGPREFIX ?= "lib"
AUTO_PACKAGE_LIBS_PROVIDEPREFIX ?= "lib"

AUTO_PACKAGE_FUNCS += "auto_package_libs"

def auto_package_libs (d):
    pn = d.getVar("PN", True)
    libs = (d.getVar("AUTO_PACKAGE_LIBS", True) or "").split()
    libdirs = (d.getVar("AUTO_PACKAGE_LIBS_LIBDIR", True) or "").split()
    pkgprefix = d.getVar("AUTO_PACKAGE_LIBS_PKGPREFIX", False) or ""
    provideprefix = d.getVar("AUTO_PACKAGE_LIBS_PROVIDEPREFIX", False) or ""
    packages = []
    dev_depends = d.getVar("AUTO_PACKAGE_LIBS_DEV_DEPENDS", True) or ""

    def get_extra_files(pkg):
        return (d.getVar("EXTRA_FILES_" + pkg, False) or "").split()

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

        pkg_rprovides = (d.getVar("RPROVIDES_" + pkg, True) or "").split()
        pkg_rprovides.append("%s%s${RE}"%(provideprefix, lib))
        d.setVar("RPROVIDES_" + pkg, " ".join(pkg_rprovides))

        devpkg_provides = (d.getVar("PROVIDES_" + devpkg, True) or "").split()
        devpkg_provides.append("%s%s${RE}"%(provideprefix, lib))
        d.setVar("PROVIDES_" + devpkg, " ".join(devpkg_provides))

        devpkg_rprovides = (d.getVar("RPROVIDES_" + devpkg, True) or "").split()
        devpkg_rprovides.append("%s%s${RE}_${PF}"%(provideprefix, lib))
        d.setVar("PROVIDES_" + pkg, " ".join(devpkg_rprovides))

        devpkg_depends = (d.getVar("DEPENDS_" + devpkg, True) or "").split()
        devpkg_depends.append("%s%s${RE}_${PF}"%(provideprefix, lib))
        devpkg_depends += dev_depends.split()
        d.setVar("DEPENDS_" + devpkg, " ".join(devpkg_depends))

    d.setVar("LIBS_AUTO_PACKAGES", " ".join(packages))
