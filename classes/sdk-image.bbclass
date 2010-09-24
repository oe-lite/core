inherit image

INHERIT_SDK_IMAGE = "tar-image"
INHERIT_SDK_IMAGE_host-mingw32 = "zip-image"
python () {
	import bb
	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)
	inherit = localdata.getVar('INHERIT_SDK_IMAGE', 1)
	d = bb.parse.handle(os.path.join('classes', '%s.bbclass' % inherit), d, True )
}

IMAGE_PREPROCESS_NETFILTER = ""
IMAGE_PREPROCESS_NETFILTER_host-mingw32 = "image_preprocess_linux_netfilter_headers"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_NETFILTER}"

image_preprocess_linux_netfilter_headers () {
	oenote image_preprocess_linux_netfilter_headers
	(
	cd ${TARGET_ARCH}/sys-root${target_includedir}/linux
	for f in netfilter*/*.h ; do
		fl=`echo $f | tr '[:upper:]' '[:lower:]'`
		if [ $fl != $f -a -f $fl ] ; then
			mv $f $f-case-conflict
		fi
	done
	)
}
