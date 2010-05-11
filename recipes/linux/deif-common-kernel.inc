require linux-deif-common.inc

KERNEL_IMAGE_BASE_NAME = "${PN}-${EPV}-${MACHINE}-${DATETIME}"
KERNEL_IMAGE_SYMLINK_NAME = "${PN}-${MACHINE}"
DTBFILE_BASE_NAME = "${MACHINE}-${PV}-${PR}-${DATETIME}"
DTBFILE_SYMLINK_NAME = "${MACHINE}"

do_compile_append() {
	oe_runmake ${MACHINE}.dtb M=arch/${ARCH}/boot CC="${KERNEL_CC}" LD="${KERNEL_LD}"
}

do_configure_append () {
        ramfs=`find ${MACHINE_SYSROOT}/*.cpio`
	cat >> ${S}/.config <<EOT
CONFIG_INITRAMFS_SOURCE="${ramfs}"
EOT
	yes '' | oe_runmake oldconfig
}

# This recipe only build image files and dtb
PROVIDES = ""
PACKAGES = "${PN}-dbg ${PN} ${PN}-dtb ${PN}-empty"
FILES_${PN} = "/${KERNEL_IMAGE_BASE_NAME}.bin"
FILES_${PN}-dtb = "/${DTBFILE_BASE_NAME}.dtb"
RDEPENDS_${PN}-dtb = "${PN}"

FILES_${PN}-empty = "/"

# trick kernel_do_install() into not installing modules
do_install_prepend () {
	mv ${S}/.config ${S}/.config.bak
	sed -e 's/CONFIG_MODULES=y/CONFIG_MODULES=n/' \
	    < ${S}/.config.bak > ${S}/.config
}

do_install_append () {
	mv ${S}/.config.bak ${S}/.config
	install -m 0644 ${S}/arch/${ARCH}/boot/${KERNEL_IMAGETYPE} \
		${D}/${KERNEL_IMAGE_BASE_NAME}.bin
	install -m 0644 ${S}/arch/${ARCH}/boot/${MACHINE}.dtb \
		${D}/${DTBFILE_BASE_NAME}.dtb
}


# and trick do_deploy() into not deploy modules tar ball
do_deploy_prepend () {
	mv ${S}/.config ${S}/.config.bak
	sed -e 's/CONFIG_MODULES=y/CONFIG_MODULES=n/' \
	    < ${S}/.config.bak > ${S}/.config
}
do_deploy_append () {
	mv ${S}/.config.bak ${S}/.config

	install -m 0644 ${S}/arch/${ARCH}/boot/${MACHINE}.dtb \
		${IMAGE_DEPLOY_DIR}/${DTBFILE_BASE_NAME}.dtb
	ln -sf ${DTBFILE_BASE_NAME}.dtb  ${IMAGE_DEPLOY_DIR}/${DTBFILE_SYMLINK_NAME}.dtb
}
