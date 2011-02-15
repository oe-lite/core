IMAGE_BASENAME ?= "${PN}-${TARGET_MACHINE_ID}"

inherit image image_mdev image_crontab image_makedevs image_inittab image_fstab
require conf/makedevs.conf

UBIFS_IMAGE_DEPENDS = "mtd-utils-native-mkfs-ubifs"
CLASS_DEPENDS += "${UBIFS_IMAGE_DEPENDS}"

IMAGE_CREATE_FUNCS += "ubifs_image"

UBIFS_IMAGE_OPTIONS += "--leb-size=${UBIFS_IMAGE_LEB_SIZE}"
UBIFS_IMAGE_OPTIONS += "--max-leb-cnt=${UBIFS_IMAGE_MAX_LEB_CNT}"
UBIFS_IMAGE_OPTIONS += "--min-io-size=${UBIFS_IMAGE_MIN_IO_SIZE}"

UBIFS_IMAGE_COMPR_TYPE ?= "lzo"
UBIFS_IMAGE_OPTIONS += "--compr=${UBIFS_IMAGE_COMPR_TYPE}"

ubifs_image () {
    mkfs.ubifs ${UBIFS_IMAGE_OPTIONS} \
        --root=${IMAGE_DIR} \
        --output=${B}/${IMAGE_BASENAME}.ubifs
}

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.ubifs ${D}/
}

FILES_${PN} += "/*.ubifs"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.ubifs \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}.ubifs
	ln -sf ${IMAGE_FULLNAME}.ubifs \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}.ubifs
}
