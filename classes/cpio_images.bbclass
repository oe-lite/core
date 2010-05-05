inherit files
inherit images

IMAGE_FILE = "${PN}-${EPV}.cpio"
FILES_${PN} = "/${IMAGE_FILE}"

create_image() {
	cd $1 && find . | cpio -o -H newc > $2 \
	|| return 1
}
