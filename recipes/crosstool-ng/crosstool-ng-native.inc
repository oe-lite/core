PR = "r0"

INHIBIT_DEFAULT_DEPS = "1"

inherit native

do_configure () {
	if [ -x ${S}/configure ] ; then
		cfgcmd="${S}/configure --prefix=${prefix} "
		oenote "Running $cfgcmd..."
		$cfgcmd || oefatal "configure failed"
	else
		oefatal "no configure script found"
	fi
}

#do_stage_install_append () {
#	mv ${STAGE_TEMP}${stage_bindir}/ct-ng \
#	   ${STAGE_TEMP}${stage_bindir}/ct-ng.orig
#	sed -e 's%${D}%$(NATIVE_DIR)%' \
#	    < ${STAGE_TEMP}${stage_bindir}/ct-ng.orig \
#	    > ${STAGE_TEMP}${stage_bindir}/ct-ng
#	rm ${STAGE_TEMP}${stage_bindir}/ct-ng.orig
#	chmod +x ${STAGE_TEMP}${stage_bindir}/ct-ng
#}
