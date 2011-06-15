#
# OE-lite class for recipes providing content for inetd.conf file
#

require conf/inetd.conf

CLASS_FLAGS += "inetd"

RDEPENDS_${PN}:>USE_inetd = " inetd"

INETD_CONF_FILES ?= "${SRCDIR}/inetd.conf"

addtask install_inetd after do_install before do_fixup
do_install_inetd[dirs] = "${D}"

do_install_inetd () {
    i=0
    test -z "${USE_inetd}" -o "${USE_inetd}"="0" || return
    for f in ${INETD_CONF_FILES} ; do
        if [ -f $f ] ; then
            # only create inetddir when needed, and let it fail silently when
            # called more than once
            mkdir -p ./${inetddir}
            let i=$i+1
            cp $f ./${inetddir}/${PN}.$i
        fi
    done
}
