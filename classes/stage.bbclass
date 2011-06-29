# -*- mode:python; -*-

inherit binconfig-stage
inherit libtool-stage
addtask stage before do_fetch

do_stage[cleandirs] =	"${STAGE_DIR}"
do_stage[dirs] =	"${STAGE_DIR}"
do_stage[recdeptask] =	"do_package"

do_stage[import] = "set_stage"
def do_stage(d):
    return set_stage(d, recipe_type_subdir=True)

def set_stage(d, recipe_type_subdir=True):
    import tempfile
    import shutil
    from oebakery import debug, info, warn, err, die

    cwd = os.getcwd()
    if not recipe_type_subdir:
        subdir = None

    stage = d.get("__stage")
    stage_files = stage.keys()
    stage_files.sort()
    for filename in stage_files:
        package = stage[filename]
        print "unpacking",filename,package
        if recipe_type_subdir:
            dstdir = os.path.join(cwd, package.type)
        else:
            dstdir = cwd

        if not os.path.isfile(filename):
            die("could not find stage file: %s"%(filename))

        print "unpacking %s to %s"%(filename, dstdir)

        unpackdir = d.getVar("STAGE_UNPACKDIR", True)
        bb.utils.mkdirhier(unpackdir)
        os.chdir(unpackdir)
        os.system("tar xpf %s"%(filename))

        d["STAGE_FIXUP_PKG_TYPE"] = package.type
        for funcname in (d.get("STAGE_FIXUP_FUNCS") or "").split():
            print "Running STAGE_FIXUP_FUNC", funcname
            function = d.get_function(funcname)
            if not function.run(unpackdir):
                return False
        del d["STAGE_FIXUP_PKG_TYPE"]

        bb.utils.mkdirhier(dstdir)

        # FIXME: do better
        for root, dirs, files in os.walk("."):
            for f in dirs:
                srcfile = os.path.join(root, f)
                dstfile = os.path.join(dstdir, srcfile)
                if os.path.isdir(dstfile):
                    continue
                if os.path.exists(dstfile):
                    warn("file exist in stage: %s" % dstfile)
                os.renames(srcfile, dstfile)
            for f in files:
                srcfile = os.path.join(root, f)
                dstfile = os.path.join(dstdir, srcfile)
                if os.path.exists(dstfile):
                    warn("file exist in stage: %s" % dstfile)
                os.renames(srcfile, dstfile)

        os.chdir(dstdir)
        shutil.rmtree(unpackdir)

STAGE_FIXUP_FUNCS ?= ""
