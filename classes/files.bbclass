def set_install(rdep,d):
    pkg = bb.data.getVar('PKGRPROVIDER_%s'%rdep, d, 0)
    if pkg:
        filename = os.path.join(bb.data.getVar('TARGET_DEPLOY_DIR', d, True),
                          pkg + '.tar')

        if not os.path.isfile(filename):
            bb.error('could not find %s to satisfy %s'%(filename, rdep))
            return False

        bb.note('Got tar package %s, unpack in %s'%(filename,os.getcwd()))

        os.system('tar -x -f %s'%filename)
    else:
        bb.note('Error getting PKGPROVIDER_%s'%rdep)
        return False

    return True

python do_files_install() {
    recrdeps = bb.data.getVar('RECRDEPENDS', d, 0)
    
    for rdep in recrdeps.split():
        if not set_install(rdep,d):
            return False
}
EXPORT_FUNCTIONS do_files_install
addtask files_install before do_files_fixup after do_install
do_files_install[cleandirs] = "${FILES_DIR}"
do_files_install[dirs] = "${FILES_DIR}"
do_files_install[recrdeptask] = "do_target_package_build"

python do_files_fixup() {
    bb.note('NI')
}
EXPORT_FUNCTIONS do_files_fixup
addtask files_fixup before do_package_install after do_files_install

