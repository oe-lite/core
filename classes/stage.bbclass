inherit binconfig-install
addtask stage before do_fetch
addtask stage_fixup after do_stage

do_stage[cleandirs] =	"${STAGE_DIR}"
do_stage[dirs] =	"${STAGE_DIR}"
do_stage[recdeptask] =	"do_package"

python do_stage () {
    import bb, tempfile
    from oebakery import debug, info, warn, err, die

    recdepends = bb.data.getVar('RECDEPENDS', d, True)
    bb.debug(1, "RECDEPENDS=%s"%recdepends)
    recdepends = recdepends.split()
    for dep in recdepends:
        bb.debug(2, 'adding build dependency %s to stage'%dep)

        # FIXME: we should find a way to avoid building recipes needed for
        # stage packages which is present (pre-baked) in deploy/stage dir.
        # perhaps we can dynamically add stage_packages to ASSUME_PROVIDED
        # in base_after_parse() based on the findings in deploy/stage
        # based on exploded DEPENDS???

        bb.note('checking %s'%(dep))

        # Get complete specification of package that provides 'dep', in
        # the form PACKAGE_ARCH/PACKAGE-PV-PR
        pkg = bb.data.getVar('PKGPROVIDER_%s'%dep, d, 0)
        debug("do_stage pkg=%s"%(pkg))
        if not pkg:
            die('PKGPROVIDER_%s not defined!'%dep)

        filename = os.path.join(bb.data.getVar('STAGE_DEPLOY_DIR', d, True),
                                pkg + '.tar')
        if not os.path.isfile(filename):
            die('could not find %s to satisfy %s'%(filename, dep))

        bb.debug(1, 'unpacking %s to %s'%(filename, os.getcwd()))

        dest = os.getcwd()
        tempdir = tempfile.mkdtemp(dir=dest)
        os.chdir(tempdir)
        bb.data.setVar('TEMP_STAGE_DIR', tempdir, d)
        # FIXME: do error handling on tar command
        os.system('tar xpf %s'%filename)
    
        for f in (bb.data.getVar('STAGE_FIXUP_FUNCS', d, 1) or '').split():
            bb.build.exec_func(f, d)
    
        # FIXME: do better
        for root, dirs, files in os.walk("."):
            for f in files:
                file = os.path.join(root, f)
                if os.path.exists(dest+"/"+file):
                    die("file exist in stage: %s" % dest+"/"+file)
                os.renames(file, dest+"/"+file)

        os.chdir(dest)

        import shutil
        shutil.rmtree(tempdir)
}

STAGE_FIXUP_FUNCS += " \
"
