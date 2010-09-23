RECIPE_OPTIONS_append += "crontab"

require conf/crontab.conf

IMAGE_PREPROCESS_CRONTAB = ""
IMAGE_PREPROCESS_CRONTAB_append_RECIPE_OPTION_crontab = "image_preprocess_crontab"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_CRONTAB}"

image_preprocess_crontab () {
	(
	cd .${crontabdir}
	for f in root.* ; do
		cat $f >> root
	rm $f
	done
	)
}
