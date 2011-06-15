require conf/makedevs.conf

CLASS_DEPENDS:>USE_makedevs = " makedevs-native"
IMAGE_PREPROCESS_FUNCS:>USE_makedevs = " image_preprocess_makedevs"

image_preprocess_makedevs () {
	if [ -d .${devtabledir} ]; then
		find ./${devtabledir}/ -type f -print0 \
			| xargs -r0 -n1 makedevs -r . -D
		rm -rf ./${devtabledir}
	fi
}
