inherit image

IMAGE_CREATE_FUNCS += "zip_image"

ZIP_IMAGE_DIRNAME ?= "${IMAGE_BASENAME}"

zip_image () {
	(
	cd `dirname ${IMAGE_DIR}`
	imagedir=`basename ${IMAGE_DIR}`
	rm -rf $imagedir.tmp
	mkdir $imagedir.tmp
	cp -a $imagedir $imagedir.tmp/${ZIP_IMAGE_DIRNAME}
	cd $imagedir.tmp
	# zip do not support dangeling symlinks so remove them
	find -L ${ZIP_IMAGE_DIRNAME} -type l -print0 | xargs -tr0 rm -f
	zip -r ${B}/${IMAGE_BASENAME}.zip ${ZIP_IMAGE_DIRNAME}
	rm -rf $imagedir.tmp
	)
}

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.zip ${D}/
}

FILES_${PN} += "/*.zip"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}.zip \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}.zip
	ln -sf ${IMAGE_FULLNAME}.zip \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}.zip
}
