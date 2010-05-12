inherit files
inherit images

IMAGE_EXT = '.tar'

create_image() {
	cd $1 \
	&& sha256sum * > sha256sum.txt \
	&& tar chf $2 . \
	|| return 1
}
