addtask set_image_stage after do_set_stage before do_compile
addtask deploy after do_install_fixup before do_build

IMAGE_BASENAME ?= "${PN}"
IMAGE_FULLNAME ?= "${IMAGE_BASENAME}-${DATETIME}"

IMAGE_PREPROCESS_FUNCS	?= ""
IMAGE_CREATE_FUNCS	?= ""

SRC_URI = ""

# FIXME: do_compile should be renamed to do_build when do_build is
# renamed to do_all, which should be done when refactoring (cleaning
# up) base.bbclass

# IMAGE_PREPROCESS_FUNCS could create device nodes, merge crontab
# entries, mdev.conf and ineted.conf files

do_compile[dirs] = "${WORKDIR}"
do_compile[cleandirs] = "${IMAGE_DIR}"

fakeroot do_compile () {
	cp -a ${IMAGE_STAGE} ${IMAGE_DIR}
	cd ${IMAGE_DIR}
	for func in ${IMAGE_PREPROCESS_FUNCS}; do
		$func
	done
	for func in ${IMAGE_CREATE_FUNCS}; do
		$func
	done
}

do_install() {
	:
}

FILES_${PN} = ""

do_deploy[dirs] = "${IMAGE_DEPLOY_DIR}"
do_deploy() {
	:
}

do_set_image_stage[dirs] = "${IMAGE_STAGE}"
do_set_image_stage[cleandirs] = "${IMAGE_STAGE}"
do_set_image_stage[recrdeptask] = "do_target_package_build"

python do_set_image_stage () {
    recrdeps = bb.data.getVar('RECRDEPENDS', d, 0)

    def image_stage_install(rdep,d):
	pkg = bb.data.getVar('PKGRPROVIDER_%s'%rdep, d, 0)
	if not pkg:
	    bb.msg.fatal(bb.msg.domain.Build, 'Error getting PKGPROVIDER_%s'%rdep)
	    return False

	filename = os.path.join(bb.data.getVar('TARGET_DEPLOY_DIR', d, True),
	     pkg + '.tar')

	if not os.path.isfile(filename):
	    bb.error('could not find %s to satisfy %s'%(filename, rdep))
	    return False

	# FIXME: extend BitBake with dependency handling that can
	# differentiate between host and target depencies for
	# canadian-cross recipes, and then cleanup this mess
	host_arch = bb.data.getVar('HOST_ARCH', d, True)
	target_arch = bb.data.getVar('TARGET_ARCH', d, True)
	if bb.data.inherits_class('canadian-cross', d) and not (pkg.startswith('sysroot/%s/'%host_arch) or pkg.startswith('sysroot/%s--'%host_arch)):
	    subdir = os.path.join(target_arch, 'sys-root')
	else:
	    subdir = ''

	bb.note('unpacking %s to %s'%(filename, os.path.abspath(subdir)))
	cmd = 'tar xpf %s'%filename
	if subdir:
	    if not os.path.exists(subdir):
		os.makedirs(subdir)
	    cmd = 'cd %s;%s'%(subdir, cmd)
	os.system(cmd)

	return True

    for rdep in recrdeps.split():
	if not image_stage_install(rdep, d):
	    bb.msg.fatal(bb.msg.domain.Build, "image_stage_install(%s) failed"%(rdep))
	    return False
}
