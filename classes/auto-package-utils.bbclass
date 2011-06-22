# -*- mode:python; -*-

PACKAGES =+ "${UTILS_AUTO_PACKAGES}"

AUTO_PACKAGE_UTILS ?= ""

addhook auto_package_utils to post_recipe_parse after base_after_parse before base_detect_machine_override fixup_package_type fixup_provides

def auto_package_utils (d):
    pn = d.getVar("PN", True)
    utils = (d.getVar("AUTO_PACKAGE_UTILS", True) or "").split()
    exeext = d.getVar("HOST_EXEEXT", True) or ""
    packages = []

    def get_extra_files(pkg):
        extra_files = d.getVar("EXTRA_FILES_" + pkg, True)
        if extra_files:
            return " " + extra_files
        return ""

    for util in utils:
        utilname = util.replace("_", "-").replace(".", "-").lower()
        pkg = "%s-%s"%(pn, utilname)
        docpkg = pkg + "-doc"
        packages += [ pkg, docpkg ]

        d.setVar("FILES_" + pkg,
                 "${base_sbindir}/%s%s "%(util, exeext) +
                 "${base_bindir}/%s%s "%(util, exeext) +
                 "${sbindir}/%s%s "%(util, exeext) +
                 "${bindir}/%s%s "%(util, exeext) +
                 get_extra_files(pkg))

        d.setVar("FILES_" + docpkg,
                 "${mandir}/man?/%s.* "%(util) +
                 get_extra_files(docpkg))

        pkg_rprovides = (d.getVar("RPROVIDES_" + pkg, True) or "").split()
        pkg_rprovides.append("util/%s"%(utilname))
        d.setVar("RPROVIDES_" + pkg, " ".join(pkg_rprovides))
    
    d.setVar("UTILS_AUTO_PACKAGES", " ".join(packages))
