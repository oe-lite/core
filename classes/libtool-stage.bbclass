STAGE_FIXUP_FUNCS += "libtool_stage_fixup"

python libtool_stage_fixup () {
    import glob, sys, os
    #print >>sys.stderr, "libtool_stage_fixup"
    tempdir = bb.data.getVar('TEMP_STAGE_DIR', d, True)
    os.chdir(tempdir)
    recipe_type = d.getVar("RECIPE_TYPE", True)
    stage_dir = os.path.realpath(d.getVar("STAGE_DIR", True))
    stage_libdir = d.getVar("stage_libdir", True).lstrip("/")
    stage_base_libdir = d.getVar("stage_base_libdir", True).lstrip("/")
    target_libdir = d.getVar("target_libdir", True).lstrip("/")
    target_base_libdir = d.getVar("target_base_libdir", True).lstrip("/")
    libdir = d.getVar("libdir", True).lstrip("/")
    base_libdir = d.getVar("base_libdir", True).lstrip("/")

    def lafile_fixup(stage_subdir, libdir, base_libdir):
        sysroot = "%s/%s"%(stage_dir, stage_subdir)
        lafiles = set(glob.glob("%s/*.la"%(libdir))).union(
                      glob.glob("%s/*.la"%(base_libdir)))
        for filename in lafiles:
            #print >>sys.stderr, "lafile_fixup %s"%(filename)
            fixed = ""
            with open(filename) as lafile:
                for line in lafile.readlines():
                    line = line.replace("-L/%s"%(libdir),
                                        "-L%s/%s"%(sysroot, libdir))
                    line = line.replace("-L/%s"%(base_libdir),
                                        "-L%s/%s"%(sysroot, base_libdir))
                    line = line.replace("libdir='/%s'"%(libdir),
                                        "libdir='%s/%s'"%(sysroot, libdir))
                    line = line.replace("libdir='/%s'"%(base_libdir),
                                        "libdir='%s/%s'"%(sysroot, base_libdir))
                    fixed += line
            with open(filename, "w") as lafile:
                lafile.write(fixed)
        return

    lafile_fixup("native", stage_libdir, stage_base_libdir)
    if recipe_type == "canadian-cross":
        lafile_fixup("host/sysroot", libdir, base_libdir)
        lafile_fixup("target/sysroot", target_libdir, target_base_libdir)
    elif recipe_type != "native":
        lafile_fixup("sysroot", libdir, base_libdir)
}
