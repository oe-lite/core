RECIPE_OPTIONS_append += "mdev"

#INHERIT_MDEV_FILES = ""
#INHERIT_MDEV_FILES_append_RECIPE_OPTION_mdev = "mdev_files"
#INHERIT += "${INHERIT_MDEV_FILES}"

require conf/mdev.conf

IMAGE_PREPROCESS_MDEV = ""
IMAGE_PREPROCESS_MDEV_append_RECIPE_OPTION_mdev = "image_stage_fixup_mdev"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_MDEV}"

image_stage_fixup_mdev () {
	test -d ./${mdevdir} || return 0
	for f in ./${mdevdir}/* ; do
		cat $f >> ./${mdevconf}
		rm $f
	done
}
