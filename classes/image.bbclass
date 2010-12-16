addtask rstage before do_compile
addtask deploy after do_fixup before do_build

IMAGE_BASENAME ?= "${PN}"
IMAGE_FULLNAME ?= "${IMAGE_BASENAME}-${DATETIME}"

IMAGE_PREPROCESS_FUNCS	?= ""
IMAGE_CREATE_FUNCS	?= ""

SRC_URI = ""

FILES_${PN} = ""

# FIXME: do_compile could be renamed to do_build when do_build is
# renamed to do_all, which should be done when merging in BitBake code
# into OE-lite Bakery as bblib.  But on the other hand, this would
# impact most recipes (those messing with do_compile(), so let's just
# stick with do_compile

# IMAGE_PREPROCESS_FUNCS could create device nodes, merge crontab
# entries, mdev.conf and ineted.conf files

do_compile[dirs] = "${IMAGE_DIR}"
do_compile[cleandirs] = "${IMAGE_DIR}"

fakeroot do_compile () {
	cp -a ${IMAGE_STAGE}/. ./
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

do_deploy[dirs] = "${IMAGE_DEPLOY_DIR}"
do_deploy() {
	:
}

do_rstage[dirs] = "${IMAGE_STAGE}"
do_rstage[cleandirs] = "${IMAGE_STAGE}"
do_rstage[recrdeptask] = "do_package"

python do_rstage () {
    recrdepends = d.getVar("RECRDEPENDS", False)
    bb.debug(1, "RECRDEPENDS=%s"%recrdepends)

    def image_stage_install(rdep):
        bb.debug(2, "adding run-time dependency %s to stage"%rdep)

        pkg = d.getVar("PKGRPROVIDER_%s"%rdep, False)
        if not pkg:
            bb.msg.fatal(bb.msg.domain.Build, "Error getting PKGPROVIDER_%s"%rdep)
            return False
        
        filename = pkg
        #filename = os.path.join(d.getVar("PACKAGE_DEPLOY_DIR", True), pkg)
        if not os.path.isfile(filename):
            bb.error("could not find %s to satisfy %s"%(filename, rdep))
            return False
        
        # FIXME: extend BitBake with dependency handling that can
        # differentiate between host and target depencies for
        # canadian-cross recipes, and then cleanup this mess
        host_arch = d.getVar("HOST_ARCH", True)
        target_arch = d.getVar("TARGET_ARCH", True)
        subdir = d.getVar("PKGSUBDIR_%s"%rdep, False)
        if (bb.data.inherits_class("canadian-cross", d) and
            subdir.startswith("target/")):
            subdir = os.path.join(target_arch, "sys-root")
        else:
            subdir = ""
        
        bb.note("unpacking %s to %s"%(filename, os.path.abspath(subdir)))
        cmd = "tar xpf %s"%filename
        if subdir:
            if not os.path.exists(subdir):
                os.makedirs(subdir)
            cmd = "cd %s;%s"%(subdir, cmd)
        os.system(cmd)

        return True

    for rdep in recrdepends.split():
        if not image_stage_install(rdep):
            bb.msg.fatal(bb.msg.domain.Build, "image_stage_install(%s) failed"%(rdep))
            return False

}
