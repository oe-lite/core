inherit tar-image-base

TAR_IMAGE_DIRNAME ?= "${IMAGE_BASENAME}"

tar_image () {
	(
	if [ -n "${TAR_IMAGE_DIRNAME}" ]; then
		cd `dirname ${IMAGE_DIR}`
		imagedir=`basename ${IMAGE_DIR}`
		rm -rf $imagedir.tmp
		mkdir $imagedir.tmp
		mv $imagedir $imagedir.tmp/${TAR_IMAGE_DIRNAME}
		ln -s $imagedir.tmp/${TAR_IMAGE_DIRNAME} $imagedir
		tar c -C $imagedir.tmp \
			-a -f ${B}/${IMAGE_BASENAME}.${TAR_IMAGE_EXT} \
			${TAR_IMAGE_DIRNAME}
		rm $imagedir
		mv $imagedir.tmp/${TAR_IMAGE_DIRNAME} $imagedir
		rmdir $imagedir.tmp
        else
		tar c -C ${IMAGE_DIR} \
			-a -f ${B}/${IMAGE_BASENAME}.${TAR_IMAGE_EXT} \
			.
	fi
	)
}
