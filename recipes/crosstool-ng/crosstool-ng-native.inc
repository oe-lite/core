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

# Let's just throw the documentation in a seperate package, which we can then
# choose to ignore
STAGE_PACKAGES += "${PN}-doc"

#python package_stage_fixup_append () { }
#do_stage_install_append () {
#	mv ${STAGE_TEMP}${stage_bindir}/ct-ng \
#	   ${STAGE_TEMP}${stage_bindir}/ct-ng.orig
#	sed -e 's%${D}%$(NATIVE_DIR)%' \
#	    < ${STAGE_TEMP}${stage_bindir}/ct-ng.orig \
#	    > ${STAGE_TEMP}${stage_bindir}/ct-ng
#	rm ${STAGE_TEMP}${stage_bindir}/ct-ng.orig
#	chmod +x ${STAGE_TEMP}${stage_bindir}/ct-ng
#}
