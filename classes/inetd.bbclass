#
# OE-lite class for recipes providing content for inetd.conf file
#

require conf/inetd.conf

RECIPE_OPTIONS_append += "inetd"

INETD_DEFAULT_RDEPENDS = ""
INETD_DEFAULT_RDEPENDS_RECIPE_OPTION_inetd = "inetd"
RDEPENDS_${PN}_append += "${INETD_DEFAULT_RDEPENDS}"

INETD_CONF_FILES ?= "${SRCDIR}/inetd.conf"

addtask install_inetd after do_install before do_fixup
do_install_inetd[dirs] = "${D}"

do_install_inetd () {
	i=0
        test -z "${RECIPE_OPTION_inetd}" -o "${RECIPE_OPTION_inetd}"="0" || return
	for f in ${INETD_CONF_FILES} ; do
		# only create inetddir when needed, and let it fail silently when
		# called more than once
		mkdir -p ./${inetddir}
		let i=$i+1
		cp $f ./${inetddir}/${PN}.$i
	done
}
