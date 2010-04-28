require linux-deif-common.inc

# Incremental PR - bump this on changes to deif-os-initramfs to
# rebuild with new initramfs.
INC_PR = "0"

# Bump this incremental PR when deif-os-initramfs is changed so we get
# deif-os-kernel rebuilt, but not linux-deif.
PR_append = ".${INC_PR}"

KERNEL_IMAGE_BASE_NAME = "${PN}-${PV}-${PR}-${MACHINE}-${DATETIME}"
KERNEL_IMAGE_SYMLINK_NAME = "${PN}-${MACHINE}"

do_compile[depends] += "deif-os-initramfs:do_build"
DEPENDS += "deif-os-initramfs linux-deif"

do_configure_append () {
	cat >> ${S}/.config <<EOT
CONFIG_INITRAMFS_SOURCE="${DEPLOY_DIR}/images/deif-os-initramfs-${MACHINE}.cpio"
EOT
	yes '' | oe_runmake oldconfig
}

# This recipe only build image files
PACKAGES = ""

# And is therefore not a real virtual/kernel provider
PROVIDES = ""

# trick kernel_do_install() into not installing modules
do_install_prepend () {
	mv ${S}/.config ${S}/.config.bak
	sed -e 's/CONFIG_MODULES=y/CONFIG_MODULES=n/' \
	    < ${S}/.config.bak > ${S}/.config
}
do_install_append () {
	mv ${S}/.config.bak ${S}/.config
}

# We don't want to stage anything
do_stage () {
	:
}

# and trick do_deploy() into not deploy modules tar ball
do_deploy_prepend () {
	mv ${S}/.config ${S}/.config.bak
	sed -e 's/CONFIG_MODULES=y/CONFIG_MODULES=n/' \
	    < ${S}/.config.bak > ${S}/.config
}
do_deploy_append () {
	mv ${S}/.config.bak ${S}/.config
}
