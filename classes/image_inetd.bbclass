CLASS_FLAGS += "inetd"

require conf/inetd.conf

IMAGE_PREPROCESS_FUNCS:>USE_inetd = " image_preprocess_inetd"

image_preprocess_inetd () {
	test -d ./${inetddir} || return 0
	for f in ./${inetddir}/* ; do
		cat $f >> ./${inetdconf}
		rm $f
	done
        rm -rf ./${inetddir}
}
