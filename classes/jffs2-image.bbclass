IMAGE_BASENAME ?= "${PN}-${TARGET_MACHINE_ID}"

require conf/makedevs.conf
inherit image image_mdev image_inetd image_crontab image_makedevs image_inittab image_fstab

JFFS2_IMAGE_DEPENDS = "mtd-utils-native-mkfs-jffs2"
CLASS_DEPENDS += "${JFFS2_IMAGE_DEPENDS}"

IMAGE_CREATE_FUNCS += "jffs2_image"

# Use lzo compression with fallback to none if low compression achieved
JFFS2_IMAGE_OPTIONS ?= "--enable-compressor=lzo --disable-compressor=zlib --disable-compressor=rtime"

jffs2_image () {
	mkfs.jffs2 ${JFFS2_IMAGE_OPTIONS} \
		--root=${IMAGE_DIR} \
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
