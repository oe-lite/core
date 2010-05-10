DESCRIPTION = "Create update image with images."
LICENSE = "GPLv2"
PR = "r2"

inherit dupdate_images

RDEPENDS = "\
dupdate-update \
deif-os-u-boot \
"

RDEPENDS_append_mpc8313erdb += "vsc7385-firmware"
