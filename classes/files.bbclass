python do_files_install() {
    recrdeps = bb.data.getVar('RECRDEPENDS', d, 0)
    files_install = bb.data.getVar('FILES_INSTALL_PACKAGE', d, True)
    for rdep in recrdeps.split():
        if not eval(files_install)(rdep, d):
            return False
}
addtask files_install before do_files_fixup after do_install
do_files_install[cleandirs] = "${FILES_DIR}"
do_files_install[dirs] = "${FILES_DIR}"
do_files_install[recrdeptask] = "do_target_package_build"


FILES_INSTALL_PACKAGE = "files_install_package"
def files_install_package(rdep,d):
    pkg = bb.data.getVar('PKGRPROVIDER_%s'%rdep, d, 0)
    if pkg:
        filename = os.path.join(bb.data.getVar('TARGET_DEPLOY_DIR', d, True),
                                pkg + '.tar')

        if not os.path.isfile(filename):
            bb.error('could not find %s to satisfy %s'%(filename, rdep))
            return False

        bb.note('unpacking %s to %s'%(filename, os.getcwd()))

        os.system('tar xpf %s'%filename)
    else:
        bb.note('Error getting PKGPROVIDER_%s'%rdep)
        return False

    return True


FILES_FIXUP_FUNCS ?= ""
python do_files_fixup() {
    for f in (bb.data.getVar('FILES_FIXUP_FUNCS', d, 1) or '').split():
        bb.build.exec_func(f, d)
}
addtask files_fixup before do_package_install after do_files_install
do_files_fixup[dirs] = "${FILES_DIR}"

RECIPE_OPTIONS_append += "mdev"

#INHERIT_MDEV_FILES = ""
#INHERIT_MDEV_FILES_append_RECIPE_OPTION_mdev = "mdev_files"
#INHERIT += "${INHERIT_MDEV_FILES}"

require conf/mdev.conf

FILES_FIXUP_MDEV = ""
FILES_FIXUP_MDEV_append_RECIPE_OPTION_mdev = "files_fixup_mdev"
FILES_FIXUP_FUNCS += "${FILES_FIXUP_MDEV}"
files_fixup_mdev[dirs] = "${FILES_DIR}"
files_fixup_mdev () {
	test -d ./${mdevdir} || return 0
	for f in ./${mdevdir}/* ; do
		cat $f >> ./${mdevconf}
		rm $f
	done
}
