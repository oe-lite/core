inherit image image_mdev image_inetd image_crontab image_makedevs image_inittab image_fstab

IMAGE_CREATE_FUNCS += "tar_image"

TAR_IMAGE_EXT ?= "tar.gz"

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.${TAR_IMAGE_EXT} ${D}/
}

FILES_${PN} += "/*.${TAR_IMAGE_EXT}"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.${TAR_IMAGE_EXT} \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}.${TAR_IMAGE_EXT}
	ln -sf ${IMAGE_FULLNAME}.${TAR_IMAGE_EXT} \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}.${TAR_IMAGE_EXT}
}
