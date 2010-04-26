DEPENDS += "makedevs-native"
PACKAGES = "${PN}"
FILES_${PN} = ""

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
#FIXME: When to run!
addtask files_install before do_files_fixup after do_compile
do_files_install[cleandirs] = "${FILES_DIR}"
do_files_install[dirs] = "${FILES_DIR}"
do_files_install[recrdeptask] = "do_files_install"#? FIXME:

python do_files_fixup() {
    bb.note('NI')
}
EXPORT_FUNCTIONS do_files_fixup
addtask files_fixup before do_files_package after do_files_install

# do_files_package()
# From machine sysroot files in FILES_DIR create machine sysroot
PACKAGES="${PN}"
FILES_${PN} = "."
python do_files_package() {
    import subprocess
    packages = (bb.data.getVar('PACKAGES', d, 1) or "").split()

    if len(packages) < 1:
        bb.debug(1, "No packages")
        return
    
    outdir = bb.data.getVar('PACKAGE_DIR_SYSROOT_MACHINE' , d, True)
    
    #FIXME: support packages
    for pkg in packages:
        bb.note("")
        # FIXME: check package arch
        pv = bb.data.getVar('EPV', d, True)
        bb.mkdirhier(outdir)
        # FIXME: add error handling for tar command
        filesdir = os.path.basename(bb.data.getVar('FILES_DIR', d, 1))
        os.system('tar cf %s/%s-%s.tar %s'%(outdir, pkg, pv, filesdir))
        bb.note('Created %s/%s-%s.tar %s'%(outdir, pkg, pv, filesdir))
}
EXPORT_FUNCTIONS do_files_package
addtask files_package before do_install after do_files_fixup
do_files_package[dirs] = "${WORKDIR}"

makedevs_files() {
    for devtable in ${1}/${devtable}/*; do
        makedevs -r ${1} -D $devtable
    done
}
