IMAGE_BASENAME ?= "${PN}-${TARGET_MACHINE_ID}"
inherit image image_mdev image_inetd image_crontab image_makedevs image_inittab image_fstab

RECIPE_OPTIONS += "ramdisk_image \
    ramdisk_image_name ramdisk_image_compression"
DEFAULT_CONFIG_ramdisk_image = "0"
DEFAULT_CONFIG_ramdisk_image_name = "${IMAGE_BASENAME}"
DEFAULT_CONFIG_ramdisk_image_compression = "none"

IMAGE_CREATE_FUNCS += "cpio_image"

inherit kernel-arch
UBOOT_ARCH = "${@map_uboot_arch('${KERNEL_ARCH}')}"
IMAGE_CREATE_FUNCS_append_RECIPE_OPTION_ramdisk_image = " cpio_mkimage"
DEPENDS_append_RECIPE_OPTION_ramdisk_image += "u-boot-tools-native-mkimage"

cpio_image () {
	(
        cd ${IMAGE_DIR}
        find . | cpio -o -H newc > ${B}/${IMAGE_BASENAME}.cpio
        cd -
	)
}

cpio_mkimage () {
	(
	case "${RECIPE_OPTION_ramdisk_image_compression}" in
		none) cp ${B}/${IMAGE_BASENAME}.cpio ${B}/image.bin
			;;
		bzip2) echo "TODO: ${RECIPE_OPTION_ramdisk_image_compression}"
			;;
		gzip) gzip ${B}/${IMAGE_BASENAME}.cpio -c > ${B}/image.bin
			;;
		lzma) echo "TODO: ${RECIPE_OPTION_ramdisk_image_compression}"
			;;
		lzo) echo "TODO: ${RECIPE_OPTION_ramdisk_image_compression}"
			;;
		*) echo "ERROR: mkimage compression ${RECIPE_OPTION_ramdisk_image_compression} not supported"
			;;
	esac

	mkimage -A ${UBOOT_ARCH} -O linux -T ramdisk \
		-C none \
		-a 0x0 -e 0x0 \
		-n ${RECIPE_OPTION_ramdisk_image_name} \
		-d ${B}/image.bin ${B}/${IMAGE_BASENAME}.img
	)
}

EXT = ".cpio"
EXT_append_RECIPE_OPTION_ramdisk_image = " .img"

do_install_append () {
	for ext in ${EXT}; do
		install -m 664 ${B}/${IMAGE_BASENAME}${ext} ${D}/
	done
}

FILES_${PN} += "/*.cpio /*.img"

do_deploy_append () {
	for ext in ${EXT}; do
		echo ${B}/${IMAGE_BASENAME}${ext} ${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}${ext}
		install -m 664 ${B}/${IMAGE_BASENAME}${ext} \
			${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}${ext}
		ln -sf ${IMAGE_FULLNAME}${ext} \
			${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}${ext}
	done
}
