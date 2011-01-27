PACKAGES =+ "${UTILS_AUTO_PACKAGES}"

AUTO_PACKAGE_UTILS ?= ""

AUTO_PACKAGE_FUNCS += "auto_package_utils"

def auto_package_utils (d):
    pn = d.getVar("PN", True)
    utils = (d.getVar("AUTO_PACKAGE_UTILS", False) or "").split()
    packages = []

    def get_extra_files(pkg):
        extra_files = d.getVar("EXTRA_FILES_" + pkg, False)
        if extra_files:
            return " " + extra_files
        return ""

    for util in utils:
        pkg = "%s-%s"%(pn, util.replace("_", "-").replace(".", "-").lower())
        docpkg = pkg + "-doc"
        packages += [ pkg, docpkg ]

        d.setVar("FILES_" + pkg,
                 "${base_sbindir}/%s "%(util) +
                 "${base_bindir}/%s "%(util) +
                 "${sbindir}/%s "%(util) +
                 "${bindir}/%s "%(util) +
                 get_extra_files(pkg))

        d.setVar("FILES_" + docpkg,
                 "${mandir}/man?/%s.* "%(util) +
                 get_extra_files(docpkg))
    
    d.setVar("UTILS_AUTO_PACKAGES", " ".join(packages))
