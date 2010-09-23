RECIPE_OPTIONS_append += "mdev"

require conf/mdev.conf

IMAGE_PREPROCESS_MDEV = ""
IMAGE_PREPROCESS_MDEV_append_RECIPE_OPTION_mdev = "image_preprocess_mdev"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_MDEV}"

image_preprocess_mdev () {
	test -d ./${mdevdir} || return 0
	for f in ./${mdevdir}/* ; do
		cat $f >> ./${mdevconf}
		rm $f
	done
}
