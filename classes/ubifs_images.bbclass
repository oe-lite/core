DEPENDS_prepend += "mtd-utils-native"

inherit files
inherit images

IMAGE_FILE = "${IMAGE_DEPLOY_DIR}/${PN}-${EPV}.ubifs"

create_image() {
	mkfs.ubifs -r $1 -o $2 \
		--leb-size=${NAND_LEB_SIZE} \
		--max-leb-cnt=${NAND_MAX_LEB_CNT} \
		--min-io-size=${NAND_MIN_IO_SIZE} \
	|| return 1
}
