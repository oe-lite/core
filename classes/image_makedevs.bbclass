RECIPE_OPTIONS_append += "makedevs"

require conf/makedevs.conf

IMAGE_PREPROCESS_MAKEDEVS = ""
IMAGE_PREPROCESS_MAKEDEVS_append_RECIPE_OPTION_makedevs = "image_preprocess_makedevs"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_MAKEDEVS}"

IMAGE_DEPENDS_MAKEDEVS = ""
IMAGE_DEPENDS_MAKEDEVS_append_RECIPE_OPTION_makedevs = "makedevs-native"
CLASS_DEPENDS += "${IMAGE_DEPENDS_MAKEDEVS}"

image_preprocess_makedevs () {
	if [ -d .${devtabledir} ]; then
		find ./${devtabledir}/ -type f -print0 \
			| xargs -r0 -n1 makedevs -r . -D
		rm -rf ./${devtabledir}
	fi
}
