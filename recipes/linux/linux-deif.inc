require linux-deif-common.inc

do_compile_append() {
	oe_runmake ${MACHINE}.dtb M=arch/${ARCH}/boot CC="${KERNEL_CC}" LD="${KERNEL_LD}"
}

do_install_append () {
	install -d ${D}${sysconfdir}/init.d
	install -m 0755 ${WORKDIR}/kernel-modules ${D}${sysconfdir}/init.d/
}

SRC_URI += "file://kernel-modules"
INITSCRIPT_PACKAGES = "${PN}-modules"
PACKAGES += "${INITSCRIPT_PACKAGES}"
INITSCRIPT_NAME_${PN}-modules = "kernel-modules"
INITSCRIPT_PARAMS_${PN}-modules = "start 11 S ."

FILES_${PN}-modules = "${sysconfdir}/init.d/kernel-modules"

#RDEPENDS_${PN}-modules = "\
#	kernel-module-physmap-of \
#	kernel-module-gen-probe \
#	kernel-module-jedec-probe \
#	kernel-module-cfi-probe \
#	kernel-module-cfi-cmdset-0002 \
#	kernel-module-cfi-util \
#	kernel-module-mtdchar \
#	kernel-module-spi-mpc8xxx \
#	kernel-module-mmc-core \
#	kernel-module-mmc-spi \
#	kernel-module-of-mmc-spi \
#	kernel-module-mmc-block \
#	kernel-module-rtc-ds1307 \
#	kernel-module-rtc-lib \
#	kernel-module-rtc-generic \
#	kernel-module-rtc-core \
#	kernel-module-ext3 \
#	kernel-module-jbd \
#	kernel-module-mbcache \
#	kernel-module-cifs \
#"

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
