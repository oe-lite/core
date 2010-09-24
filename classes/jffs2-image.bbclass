inherit image image_mdev image_crontab image_makedevs

IMAGE_CREATE_FUNCS += "jffs2_image"

jffs2_image () {
	mkfs.jffs2 -x lzo --root=${IMAGE_STAGE} --faketime \
		--output=${B}/${IMAGE_BASENAME}.jffs2
}

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.jffs2 ${D}/
}

FILES_${PN} += "/${IMAGE_BASENAME}.jffs2*"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.jffs2 \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}.jffs2
	ln -sf ${IMAGE_FULLNAME}.jffs2 \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}.jffs2
}
