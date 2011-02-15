IMAGE_BASENAME ?= "${PN}-${TARGET_MACHINE_ID}"

inherit image image_mdev image_crontab image_makedevs image_inittab
require conf/makedevs.conf

IMAGE_CREATE_FUNCS += "cpio_image"

CPIO_IMAGE_DIRNAME ?= "${IMAGE_BASENAME}"

cpio_image () {
	(
        cd ${IMAGE_DIR}
        find . | cpio -o -H newc > ${B}/${IMAGE_BASENAME}.cpio
        cd -
	)
}

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.cpio ${D}/
}

FILES_${PN} += "/*.cpio"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.cpio \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}.cpio
	ln -sf ${IMAGE_FULLNAME}.cpio \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}.cpio
}
