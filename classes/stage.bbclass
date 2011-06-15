# -*- mode:python; -*-

inherit binconfig-stage
inherit libtool-stage
addtask stage before do_fetch
addtask stage_fixup after do_stage

do_stage[cleandirs] =	"${STAGE_DIR}"
do_stage[dirs] =	"${STAGE_DIR}"
do_stage[recdeptask] =	"do_package"

python do_stage () {
    import bb, tempfile, shutil
    from oebakery import debug, info, warn, err, die

    recdepends = d.getVar("RECDEPENDS", False)
    recdepends = recdepends.split()
    cwd = os.getcwd()
    for dep in recdepends:
        bb.debug(2, "adding build dependency %s to stage"%dep)

        # Get complete specification of package that provides "dep", in
        # the form PACKAGE_ARCH/PACKAGE_PV-PR_buildhash
        pkg = d.getVar("PKGPROVIDER_%s"%dep, False)
        if not pkg:
            die("PKGPROVIDER_%s not defined!"%dep)

        subdir = d.getVar("PKGSUBDIR_%s"%dep, False)
        if not subdir:
            die("PKGSUBDIR_%s not defined!"%dep)

        debug("do_stage pkg=%s subdir=%s"%(pkg, subdir))

        filename = os.path.join(d.getVar("PACKAGE_DEPLOY_DIR", True), pkg)
        if not os.path.isfile(filename):
            die("could not find %s to satisfy %s"%(filename, dep))

        if subdir:
            dstdir = os.path.join(cwd, subdir)
        else:
            dstdir = cwd

        bb.debug(1, "unpacking %s to %s"%(filename, dstdir))

        unpackdir = d.getVar("STAGE_UNPACKDIR", True)
        bb.utils.mkdirhier(unpackdir)
        os.chdir(unpackdir)
        os.system("tar xpf %s"%filename)
        d.setVar("STAGE_FIXUP_SUBDIR", subdir)

        for f in (bb.data.getVar("STAGE_FIXUP_FUNCS", d, 1) or "").split():
            bb.build.exec_func(f, d)

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
}

STAGE_FIXUP_FUNCS ?= ""
