addtask set_stage before do_fetch

do_set_stage[cleandirs] =	"${STAGE_DIR}"
do_set_stage[dirs] =		"${STAGE_DIR}"
do_set_stage[recdeptask] =	"do_stage_package_build"

python do_set_stage () {
    import bb

    recdepends = bb.data.getVar('RECDEPENDS', d, True).split()
    bb.debug('set_stage: RECDEPENDS=%s'%recdepends)
    for dep in recdepends:
	set_stage_add(dep, d)
}

def set_stage_add(dep, d):
    bb.debug(2, 'adding build dependency %s to stage'%dep)

    # FIXME: we should find a way to avoid building recipes needed for
    # stage packages which is present (pre-baked) in deploy/stage dir.
    # perhaps we can dynamically add stage_packages to ASSUME_PROVIDED
    # in base_after_parse() based on the findings in deploy/stage
    # based on exploded DEPENDS???

    # Get complete specification of package that provides 'dep', in
    # the form PACKAGE_ARCH/PACKAGE-PV-PR
    pkg = bb.data.getVar('PKGPROVIDER_%s'%dep, d, 0)
    if not pkg:
	bb.error('PKGPROVIDER_%s not defined!'%dep)
	return

    filename = os.path.join(bb.data.getVar('STAGE_DEPLOY_DIR', d, True), pkg + '.tar')
    if not os.path.isfile(filename):
	bb.error('could not find %s to satisfy %s'%(filename, dep))
	return

    bb.note('unpacking %s to %s'%(filename, os.getcwd()))

    # FIXME: do error handling on tar command
    os.system('tar xfp %s'%filename)
    return
