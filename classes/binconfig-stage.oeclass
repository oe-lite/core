# -*- mode:python; -*-

require conf/meta.conf

STAGE_FIXUP_FUNCS += "binconfig_stage_fixup"

def binconfig_stage_fixup(d):
    import re, fileinput, os

    metafile = d.getVar("binconfigfilelist", True).lstrip("/")
    if not os.path.exists(metafile):
        return

    binconfig_files = open(metafile, "r")

    stage_dir = os.path.realpath(d.getVar("STAGE_DIR", True))
    subdir = d.getVar("STAGE_FIXUP_SUBDIR", False)
    sysroot = os.path.join(stage_dir, subdir)

    if subdir in ("native", "cross", "sdk-cross"):
        dirname_prefix = "stage_"
    elif subdir == "canadian-cross":
        dirname_prefix = "target_"
    else:
        dirname_prefix = ""

    dirnames = ("prefix", "exec_prefix", "bindir", "sbindir",
                "libdir", "includedir", "libexecdir",
                "datadir", "sysconfdir", "sharedstatedir", "localstatedir",
                "infodir", "mandir")
    dirpaths = {}
    for dirname in dirnames:
        dirpaths[dirname] = d.getVar(dirname_prefix + dirname, True)

    for filename in binconfig_files:
        filename = filename.strip()

        with open(filename, "r") as input_file:
            binconfig_file = input_file.read()

        for dirname in dirnames:
            binconfig_file = re.sub(
                re.compile("^(%s=).*"%(dirname), re.MULTILINE),
                r"\g<1>%s/%s"%(sysroot, dirpaths[dirname]),
                binconfig_file)

        for flagvar in ("CPPFLAGS", "CFLAGS", "CXXFLAGS", "LDFLAGS"):
            binconfig_file = re.sub(
                 re.compile("^(%s=[\"'])"%(flagvar), re.MULTILINE),
                 r"\g<1>--sysroot=%s "%(sysroot),
                 binconfig_file)

        for option in ("-isystem ", "-I", "-iquote"):
            binconfig_file = re.sub(
                re.compile("^(%s)(%s)"%(option, dirpaths["includedir"]), re.MULTILINE),
                r"\g<1>%s\g<2>"%(sysroot),
                binconfig_file)

        for option in ("-L"):
            binconfig_file = re.sub(
                re.compile("^(%s)(%s)"%(option, dirpaths["libdir"]), re.MULTILINE),
                r"\g<1>%s\g<2>"%(sysroot),
                binconfig_file)

        with open(filename, "w") as output_file:
            output_file.write(binconfig_file)

    os.unlink(metafile)
