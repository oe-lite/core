# -*- mode:python; -*-

PACKAGES =+ "${LIBS_AUTO_PACKAGES}"
PACKAGES[expand] = 3

AUTO_PACKAGE_LIBS ?= ""
AUTO_PACKAGE_LIBS_LIBDIR ?= "${libdir}"
AUTO_PACKAGE_LIBS_PKGPREFIX ?= "lib"
AUTO_PACKAGE_LIBS_PROVIDEPREFIX ?= "lib"
AUTO_PACKAGE_LIBS_DEV_DEPENDS ?= ""
AUTO_PACKAGE_LIBS_DEV_RDEPENDS ?= "${AUTO_PACKAGE_LIBS_DEV_DEPENDS}"

addhook auto_package_libs to post_recipe_parse after base_after_parse before fixup_package_type fixup_provides

def auto_package_libs (d):
    import warnings

    pn = d.getVar("PN", True)
    libs = (d.getVar("AUTO_PACKAGE_LIBS", True) or "").split()
    libdirs = (d.getVar("AUTO_PACKAGE_LIBS_LIBDIR", True) or "").split()
    pkgprefix = d.getVar("AUTO_PACKAGE_LIBS_PKGPREFIX", True) or ""
    provideprefix = d.getVar("AUTO_PACKAGE_LIBS_PROVIDEPREFIX", True) or ""
    pcprefixes = (d.get("AUTO_PACKAGE_LIBS_PCPREFIX") or "").split()
    packages = []
    dev_depends = d.get("AUTO_PACKAGE_LIBS_DEV_DEPENDS") or ""
    dev_rdepends = d.get("AUTO_PACKAGE_LIBS_DEV_RDEPENDS")
    if dev_rdepends is None:
        dev_rdepends = dev_depends

    def get_extra_files(pkg):
        #return (d.get("FILES_" + pkg) or "").split()
        files = d.get("FILES_" + pkg)
        if files is None:
            files = d.get("EXTRA_FILES_" + pkg)
            if files:
                warnings.warn(
                    "EXTRA_FILES_* is deprecated, use FILES_* instead")
        return (files or "").split()

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
        elif libdir[3]:
            libdir[3] = libdir[3].split(",")
        if len(libdir) < 5:
            libdir.append("${SOLIBSDEV},.la,.a".split(","))
        elif libdir[4]:
            libdir[4] = libdir[4].split(",")
        return libdir

    for lib in libs:
        pkg = "%s-%s%s"%(pn, pkgprefix, lib.replace("_", "-").lower())
        devpkg = pkg + "-dev"
        packages += [ pkg, devpkg ]

        files = []
        pkg_libsuffix = d.getVar("LIBSUFFIX_%s"%(pkg), True)
        for libdir in libdirs:
            (libdir, libprefix, libsuffix, libexts, devlibexts) = split_libdir(libdir)
            if pkg_libsuffix is not None:
                libsuffix = pkg_libsuffix
            libname = "%s%s%s"%(libprefix, lib, libsuffix)
            for libext in libexts:
                files.append("%s/%s%s"%(libdir, libname, libext))
        files += get_extra_files(pkg)
        d.set("FILES_" + pkg, " ".join(files))

        files = []
        pkg_libsuffix = d.getVar("LIBSUFFIX_%s"%(pkg), True)
        for libdir in libdirs:
            (libdir, libprefix, libsuffix, libexts, devlibexts) = split_libdir(libdir)
            if pkg_libsuffix is not None:
                libsuffix = pkg_libsuffix
            libname = "%s%s%s"%(libprefix, lib, libsuffix)
            for libext in devlibexts:
                files.append("%s/%s%s"%(libdir, libname, libext))
            if pkg_libsuffix is None:
                for pcprefix in pcprefixes:
                    pcfile = "${libdir}/pkgconfig/%s%s%s.pc"%(
                        pcprefix, lib, libsuffix)
                    if not pcfile in files:
                        files.append(pcfile)
        if pkg_libsuffix is not None:
            for pcprefix in pcprefixes:
                pcfile = "${libdir}/pkgconfig/%s%s%s.pc"%(
                    pcprefix, lib, pkg_libsuffix)
                if not pcfile in files:
                    files.append(pcfile)
        files += get_extra_files(devpkg)
        d.set("FILES_" + devpkg, " ".join(files))

        pkg_provides = (d.getVar("PROVIDES_" + pkg, True) or "").split()
        pkg_provides.append("%s%s"%(provideprefix,
                                    lib.replace("_", "-").lower()))
        d.set("PROVIDES_" + pkg, " ".join(pkg_provides))

        devpkg_provides = (d.getVar("PROVIDES_" + devpkg, True) or "").split()
        devpkg_provides.append("%s%s-dev"%(provideprefix,
                                           lib.replace("_", "-").lower()))
        d.set("PROVIDES_" + devpkg, " ".join(devpkg_provides))

        pkg_depends = (d.getVar("DEPENDS_" + pkg, True) or "").split()

        pkg_rdepends = d.get("RDEPENDS_" + pkg, True)
        if pkg_rdepends is None:
            pkg_rdepends = []
            for dep in pkg_depends:
                if dep.startswith("lib"):
                    pkg_rdepends.append(dep)
        else:
            pkg_rdepends = pkg_rdepends.split()
        d.set("RDEPENDS_" + pkg, " ".join(pkg_rdepends))

        pkg_depends.append("%s_${PV}"%(devpkg))
        d.set("DEPENDS_" + pkg, " ".join(pkg_depends))

        devpkg_depends = (d.getVar("DEPENDS_" + devpkg, True) or "").split()
        devpkg_depends += dev_depends.split()
        d.set("DEPENDS_" + devpkg, " ".join(devpkg_depends))

        devpkg_rdepends = d.getVar("RDEPENDS_" + devpkg, True)
        if devpkg_rdepends is None:
            devpkg_rdepends = []
            for dep in pkg_rdepends:
                if dep.endswith("-dev"):
                    devpkg_rdepends.append(dep)
                else:
                    devpkg_rdepends.append(dep + "-dev")
        else:
            devpkg_rdepends = devpkg_rdepends.split()
        devpkg_rdepends.append("%s_${PV}"%(pkg))
        devpkg_rdepends += dev_rdepends.split()
        d.set("RDEPENDS_" + devpkg, " ".join(devpkg_rdepends))

    d.set("LIBS_AUTO_PACKAGES", " ".join(packages))
