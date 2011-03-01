inherit image image_mdev image_inetd image_crontab image_makedevs image_inittab image_fstab

IMAGE_CREATE_FUNCS += "tar_image"

TAR_IMAGE_EXT ?= "tar.gz"
TAR_IMAGE_DIRNAME ?= "${IMAGE_BASENAME}"

tar_image () {
	(
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
	)
}

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
