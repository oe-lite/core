IMAGE_BASENAME ?= "${PN}-${TARGET_MACHINE_ID}"

inherit image image_mdev image_inetd image_crontab image_makedevs image_inittab image_fstab

EXT2_IMAGE_DEPENDS = "native:genext2fs"
CLASS_DEPENDS += "${EXT2_IMAGE_DEPENDS}"

IMAGE_CREATE_FUNCS += "genext2fs_image"

EXT2_IMAGE_SIZE ?= "20480"
EXT2_IMAGE_OPTIONS ?= "-z -q -f -b ${EXT2_IMAGE_SIZE}"

genext2fs_image () {
	genext2fs ${EXT2_IMAGE_OPTIONS} \
		 -d ${IMAGE_DIR} \
		 ${B}/${IMAGE_BASENAME}.ext2
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
