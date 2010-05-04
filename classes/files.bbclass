DEPENDS += "makedevs-native"
PACKAGES = "${PN}"
FILES_${PN} = ""

def set_install(rdep,d):
    pkg = bb.data.getVar('PKGPROVIDER_%s'%rdep, d, 0)
    if rdep == 'libc':
        pkg = 'libc'
    elif rdep == 'base-files':
        pkg = 'base-files-0.1-r0'
    elif rdep == 'busybox':
        pkg = 'busybox-1.16.0-r21.1'
    elif rdep == 'mtd-utils':
        pkg = 'mtd-utils-1.3.1-r3'
    elif rdep == 'lzo':
        pkg = 'lzo-2.02-r1'
    elif rdep == 'zlib':
        pkg = 'zlib-1.2.4-r1'
    elif rdep == 'util-linux-ng':
        pkg = 'util-linux-ng-2.17.2-r1.1'
    elif rdep == 'test':
        pkg = 'test-1-r0'
    else:
        bb.note('No PKG %s' + rdep)
    
    if pkg:
        filename = os.path.join(bb.data.getVar('PACKAGE_DIR_SYSROOT_MACHINE', d, True), pkg + '.tar')
        if not os.path.isfile(filename):
            bb.error('could not find %s to satisfy %s'%(filename, rdep))
            return
        bb.note('Got tar package %s, unpack in %s'%(filename,os.getcwd()))

        # Unpack machine packages into files
        os.system('tar -x --transform \'s#^machine##g\' -f %s'%filename)
    else:
        bb.note('Error getting PKGPROVIDER_%s'%rdep)
    return

python do_files_install() {
    # FIXME: Do not explode RDEPENDS on files packages (they already
    # contain exploded RDEPS)
    #rdepends = bb.utils.explode_deps(bb.data.getVar('RDEPENDS', d, True))
    # Above does not work
    #bb.utils.explode_deps(bb.data.getVar('RDEPENDS_' + pkg, d, True)
    rdepends = ['libc', 'base-files', 'busybox', 'mtd-utils', 'zlib', 'lzo', 'util-linux-ng']

    for rdep in rdepends:
        set_install(rdep,d)
}
EXPORT_FUNCTIONS do_files_install
#FIXME: When to run!
addtask files_install before do_files_fixup after do_compile
do_files_install[cleandirs] = "${FILES_DIR}"
do_files_install[dirs] = "${FILES_DIR}"
do_files_install[recrdeptask] = "do_target_package_build"

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
