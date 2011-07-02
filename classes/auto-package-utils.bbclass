# -*- mode:python; -*-

PACKAGES =+ "${AUTO_PACKAGE_UTILS_PACKAGES}"

AUTO_PACKAGE_UTILS ?= ""

addhook auto_package_utils to post_recipe_parse after base_after_parse before base_detect_machine_override fixup_package_type fixup_provides

def auto_package_utils (d):
    import warnings

    pn = d.get("PN")
    utils = (d.get("AUTO_PACKAGE_UTILS") or "").split()
    exeext = d.get("HOST_EXEEXT") or ""
    packages = []
    provides = []

    def get_extra_files(pkg):
        #return (d.get("FILES_" + pkg) or "").split()
        files = d.get("FILES_" + pkg)
        if files is None:
            files = d.get("EXTRA_FILES_" + pkg)
            if files:
                warnings.warn(
                    "EXTRA_FILES_* is deprecated, use FILES_* instead")
        return (files or "").split()

    for util in utils:
        utilname = util.replace("_", "-").replace(".", "-").lower()
        pkg = "%s-%s"%(pn, utilname)
        utilname = "util/" + utilname
        docpkg = pkg + "-doc"
        packages += [ pkg, docpkg ]
        provides += [ utilname ]

        d.set("FILES_" + pkg,
              "${base_sbindir}/%s%s "%(util, exeext) +
              "${base_bindir}/%s%s "%(util, exeext) +
              "${sbindir}/%s%s "%(util, exeext) +
              "${bindir}/%s%s "%(util, exeext) +
              " ".join(get_extra_files(pkg)))

        d.set("FILES_" + docpkg,
              "${mandir}/man?/%s.* "%(util) +
              " ".join(get_extra_files(docpkg)))

        pkg_provides = (d.get("PROVIDES_" + pkg) or "").split()
        pkg_provides.append(utilname)
        d.set("PROVIDES_" + pkg, " ".join(pkg_provides))
    
    d.set("AUTO_PACKAGE_UTILS_PACKAGES", " ".join(packages))
    d.set("AUTO_PACKAGE_UTILS_PROVIDES", " ".join(provides))
