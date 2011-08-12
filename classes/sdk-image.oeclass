inherit image

INHERIT_SDK_IMAGE = "tar-image"
INHERIT_SDK_IMAGE:HOST_OS-mingw32 = "zip-image"
inherit ${INHERIT_SDK_IMAGE}
#python () {
#    import bb
#    localdata = bb.data.createCopy(d)
#    bb.data.update_data(localdata)
#    inherit = localdata.getVar('INHERIT_SDK_IMAGE', 1)
#    d = bb.parse.handle(os.path.join('classes', '%s.bbclass' % inherit), d, True )
#}

IMAGE_PREPROCESS_NETFILTER = ""
IMAGE_PREPROCESS_NETFILTER:HOST_OS-mingw32 = "image_preprocess_linux_netfilter_headers"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_NETFILTER}"

image_preprocess_linux_netfilter_headers () {
	oenote image_preprocess_linux_netfilter_headers
	(
	cd ${TARGET_ARCH}/sysroot${target_includedir}/linux
	for f in netfilter*/*.h ; do
		fl=`echo $f | tr '[:upper:]' '[:lower:]'`
		if [ $fl != $f -a -f $fl ] ; then
			mv $f $f-case-conflict
		fi
	done
	)
}
