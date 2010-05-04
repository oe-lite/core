require linux-deif-common.inc

do_compile_append() {
	oe_runmake ${MACHINE}.dtb M=arch/${ARCH}/boot CC="${KERNEL_CC}" LD="${KERNEL_LD}"
}

do_install_append () {
	install -d ${D}${sysconfdir}/init.d
	install -d ${D}${sysconfdir}/rcS.d/
	install -m 0755 ${WORKDIR}/kernel-modules ${D}${sysconfdir}/init.d/
	ln -s ../init.d/kernel-modules ${D}${sysconfdir}/rcS.d/S11kernel-modules
}

SRC_URI += "file://kernel-modules"
FILES_${PN}-modules = "${sysconfdir}/init.d/kernel-modules ${sysconfdir}/rcS.d/S11kernel-modules"

PACKAGES += "${PN}-modules"

RDEPENDS_${PN}-modules = "\
kernel-module-i2c \
kernel-module-mmc \
kernel-module-mmc-test \
kernel-module-mtd \
kernel-module-mtd-test \
kernel-module-rtc \
kernel-module-spi \
kernel-module-fs \
"

do_stage_append() {
	install -m 0644 arch/${ARCH}/boot/${MACHINE}.dtb \
		${STAGING_KERNEL_DIR}/${MACHINE}.dtb-${KERNEL-VERSION}
}

DTBFILE_BASE_NAME ?= "${MACHINE}-${PV}-${PR}-${DATETIME}.dtb"
DTBFILE_SYMLINK_NAME ?= "${MACHINE}.dtb"

do_deploy_append() {
	install -d ${DEPLOY_DIR_IMAGE}
	install -m 0644 ${S}/arch/${ARCH}/boot/${MACHINE}.dtb \
		${DEPLOY_DIR_IMAGE}/${DTBFILE_BASE_NAME}
	package_stagefile_shell ${DEPLOY_DIR_IMAGE}/${DTBFILE_BASE_NAME}
	cd ${DEPLOY_DIR_IMAGE}
	rm -f ${DTBFILE_SYMLINK_NAME}
	ln -sf ${DTBFILE_BASE_NAME} ${DTBFILE_SYMLINK_NAME}
	package_stagefile_shell ${DEPLOY_DIR_IMAGE}/${DTBFILE_SYMLINK_NAME}
}
