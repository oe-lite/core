inherit tar-image-base


tar_image () {
	(
	tar c -C ${IMAGE_DIR} \
		-a -f ${B}/${IMAGE_BASENAME}.${TAR_IMAGE_EXT} \
		.
	)
}

