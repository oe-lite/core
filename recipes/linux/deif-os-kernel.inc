require linux-deif-common.inc

# Incremental PR - bump this on changes to deif-os-initramfs to
# rebuild with new initramfs.
INC_PR = "0"

# Bump this incremental PR when deif-os-initramfs is changed so we get
# deif-os-kernel rebuilt, but not linux-deif.
PR_append = ".${INC_PR}"

KERNEL_IMAGE_BASE_NAME = "${PN}-${PV}-${PR}-${MACHINE}-${DATETIME}"
KERNEL_IMAGE_SYMLINK_NAME = "${PN}-${MACHINE}"
DTBFILE_BASE_NAME = "${MACHINE}-${PV}-${PR}-${DATETIME}"
DTBFILE_SYMLINK_NAME = "${MACHINE}"

DEPENDS += "deif-os-initramfs"

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
PACKAGES =+ "${PN} ${PN}-dtb"
FILES_${PN} = "/${KERNEL_IMAGE_SYMLINK_NAME}.bin"
FILES_${PN}-dtb = "/${DTBFILE_SYMLINK_NAME}.dtb"

PROVIDES_${PN} = "${PN} ${PN}-dtb"

# trick kernel_do_install() into not installing modules
do_install_prepend () {
	mv ${S}/.config ${S}/.config.bak
	sed -e 's/CONFIG_MODULES=y/CONFIG_MODULES=n/' \
	    < ${S}/.config.bak > ${S}/.config
}

do_install_append () {
	mv ${S}/.config.bak ${S}/.config
	install -m 0644 ${S}/arch/${ARCH}/boot/${KERNEL_IMAGETYPE} \
		${D}/${KERNEL_IMAGE_SYMLINK_NAME}.bin
	install -m 0644 ${S}/arch/${ARCH}/boot/${MACHINE}.dtb \
		${D}/${DTBFILE_SYMLINK_NAME}.bin
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
	package_stagefile_shell ${IMAGE_DEPLOY_DIR}/${DTBFILE_BASE_NAME}.dtb
	cd ${IMAGE_DEPLOY_DIR}
	rm -f ${DTBFILE_SYMLINK_NAME}.dtb
	ln -sf ${DTBFILE_BASE_NAME}.dtb ${DTBFILE_SYMLINK_NAME}.dtb
	package_stagefile_shell ${IMAGE_DEPLOY_DIR}/${DTBFILE_SYMLINK_NAME}.dtb

}
