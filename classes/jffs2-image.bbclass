IMAGE_BASENAME ?= "${PN}-${TARGET_MACHINE_ID}"

inherit image image_mdev image_crontab image_makedevs

JFFS2_IMAGE_DEPENDS = "mtd-utils-native-mkfs"
CLASS_DEPENDS += "${JFFS2_IMAGE_DEPENDS}"

IMAGE_CREATE_FUNCS += "jffs2_image"

JFFS2_IMAGE_OPTIONS ?= "-x lzo --faketime"

jffs2_image () {
	mkfs.jffs2 ${JFFS2_IMAGE_OPTIONS} \
		--root=${IMAGE_STAGE} \
		--output=${B}/${IMAGE_BASENAME}.jffs2
}

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.jffs2 ${D}/
}

FILES_${PN} += "/*.jffs2"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.jffs2 \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}.jffs2
	ln -sf ${IMAGE_FULLNAME}.jffs2 \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}.jffs2
}
