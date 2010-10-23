IMAGE_BASENAME ?= "${PN}-${TARGET_MACHINE_ID}"

inherit image image_mdev image_crontab image_makedevs

EXT2_IMAGE_DEPENDS = "genext2fs-native"
CLASS_DEPENDS += "${EXT2_IMAGE_DEPENDS}"

IMAGE_CREATE_FUNCS += "genext2fs_image"

EXT2_IMAGE_SIZE ?= "20480"
EXT2_IMAGE_OPTIONS ?= "-z -q -f"

genext2fs_image () {
	genext2fs -b ${EXT2_IMAGE_SIZE} -d ${IMAGE_STAGE} ${EXT2_IMAGE_OPTIONS} ${B}/${IMAGE_BASENAME}.ext2
}

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.ext2 ${D}/
}

FILES_${PN} += "/*.ext2"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.ext2 \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}.ext2
	ln -sf ${IMAGE_FULLNAME}.ext2 \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}.ext2
}
