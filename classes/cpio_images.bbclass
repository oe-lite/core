inherit files
inherit images

IMAGE_FILE = "${IMAGE_DEPLOY_DIR}/${PN}-${EPV}.cpio"

create_image() {
	cd $1 && find . | cpio -o -H newc > $2 \
	|| return 1
}
