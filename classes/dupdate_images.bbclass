inherit files
inherit images

IMAGE_FILE = "${PN}-${EPV}.tar"
FILES_${PN} = "/${IMAGE_FILE}"

create_image() {
	cd $1 \
	&& sha256sum * > sha256sum.txt \
	&& tar chf $2 . \
	|| return 1
}
