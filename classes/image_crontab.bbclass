require conf/crontab.conf

IMAGE_PREPROCESS_FUNCS:>USE_crontab = " image_preprocess_crontab"

image_preprocess_crontab () {
	(
	cd .${crontabdir}
	for f in root.* ; do
		cat $f >> root
	rm $f
	done
	)
}
