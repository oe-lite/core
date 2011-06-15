#
# OE-lite class for handling fstab file.
#
# Inherit this class in recipes needing to add stuff to /etc/fstab .
# Recipes install task should install the required content into the
# /etc/fstab file, and the fixup_fstab will relocate this to
# /etc/fstab.d/${PN} which will the be merged with the (master)
# /etc/fstab file together with other additions in the compile task
# of image builds.
#

require conf/fstab.conf

FIXUP_FUNCS += "fstab_fixup"

RDEPENDS_${PN}:>USE_fstab += " util/mount"

fstab_fixup[dirs] = "${D}"

fstab_fixup () {
    echo fstab_fixup
    set -e
    pwd
    tree
    if [ -e .${sysconfdir}/fstab ] ; then
        mkdir -p .${fstabfixupdir}
        mv .${sysconfdir}/fstab .${fstabfixupdir}/${PN}
    fi
}
