PR = "r0"

INHIBIT_DEFAULT_DEPS = "1"

inherit native

do_configure () {
	if [ -x ${S}/configure ] ; then
		cfgcmd="${S}/configure --prefix=${D}${prefix} "
		oenote "Running $cfgcmd..."
		$cfgcmd || oefatal "configure failed"
	else
		oefatal "no configure script found"
	fi
}

FILES_${PN} += "${libdir}/ct-ng-${PV}"

stage_package_fixup () {
	mv ${PN}/${stage_bindir}/ct-ng \
	   ${PN}${stage_bindir}/ct-ng.orig
	sed -e 's%${D}%$(NATIVE_DIR)%' \
	    < ${PN}${stage_bindir}/ct-ng.orig \
	    > ${PN}${stage_bindir}/ct-ng
	rm ${PN}${stage_bindir}/ct-ng.orig
	chmod +x ${PN}${stage_bindir}/ct-ng
}
