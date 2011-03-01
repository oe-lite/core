RECIPE_OPTIONS_append += "inetd"

require conf/inetd.conf

IMAGE_PREPROCESS_INETD = ""
IMAGE_PREPROCESS_INETD_append_RECIPE_OPTION_inetd = "image_preprocess_inetd"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_INETD}"

image_preprocess_inetd () {
	test -d ./${inetddir} || return 0
	for f in ./${inetddir}/* ; do
		cat $f >> ./${inetdconf}
		rm $f
	done
        rm -rf ./${inetddir}
}
