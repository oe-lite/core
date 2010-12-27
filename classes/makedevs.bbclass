addtask install_makedevs after do_install before do_fixup

RECIPE_OPTIONS_append += "makedevs"

require conf/makedevs.conf

do_install_makedevs[dirs] = "${D}"

do_install_makedevs () {
	if [ -z "${MAKEDEVS_FILES}" ]; then
		return
	fi
	install -m 0755 -d ${D}${devtabledir}
	i=1
	for f in ${MAKEDEVS_FILES} ; do
		install -m 0644 $f ${D}${devtabledir}/${PN}.$i
		i=$((i+1))
	done
}
