#
# OE-lite class for handling inittab file.
#
# Inherit this class in recipes needing to add stuff to /etc/inittab .
# Recipes install task should install the required content into the
# /etc/inittab file, and the fixup_inittab will relocate this to
# /etc/inittab.d/${PN} which will the be merged with the (master)
# /etc/inittab file together with other additions in the compile task
# of image builds.
#

require conf/inittab.conf

FIXUP_FUNCS += "inittab_fixup"

INITTAB_DEFAULT_RDEPENDS = ""
INITTAB_DEFAULT_RDEPENDS_RECIPE_OPTION_inittab = "feature/sysvinit"
RDEPENDS_${PN}_append += "${INITTAB_DEFAULT_RDEPENDS}"

inittab_fixup[dirs] = "${D}"

inittab_fixup () {
    echo inittab_fixup
    set -e
    pwd
    tree
    if [ -e .${sysconfdir}/inittab ] ; then
        mkdir -p .${inittabfixupdir}
        mv .${sysconfdir}/inittab .${inittabfixupdir}/${PN}
    fi
}
