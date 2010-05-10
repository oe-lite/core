DESCRIPTION = "U-boot bootloader"
HOMEPAGE = "http://u-boot.sf.net"
SECTION = "bootloaders"
PRIORITY = "optional"
LICENSE = "GPL"
PROVIDES_${PN} = "virtual/bootloader"

PARALLEL_MAKE=""

EXTRA_OEMAKE = "CROSS_COMPILE=${TARGET_PREFIX}"
FILES_${PN} = "/"
UBOOT_MACHINE ?= "${MACHINE}_config"
UBOOT_IMAGE ?= "u-boot-${MACHINE}-${PV}-${PR}.bin"
UBOOT_SYMLINK ?= "u-boot-${MACHINE}.bin"

do_compile () {
	unset LDFLAGS
	unset CFLAGS
	unset CPPFLAGS
	oe_runmake ${UBOOT_MACHINE}
	oe_runmake all
}

do_install () {
	install ${S}/u-boot.bin ${D}/${UBOOT_IMAGE}
}

do_deploy () {
	install -d ${IMAGE_DEPLOY_DIR}
	install ${S}/u-boot.bin ${IMAGE_DEPLOY_DIR}/${UBOOT_IMAGE}
	package_stagefile_shell ${IMAGE_DEPLOY_DIR}/${UBOOT_IMAGE}

	cd ${IMAGE_DEPLOY_DIR}
	rm -f ${UBOOT_SYMLINK}
	ln -sf ${UBOOT_IMAGE} ${UBOOT_SYMLINK}
	package_stagefile_shell ${IMAGE_DEPLOY_DIR}/${UBOOT_SYMLINK}
}
do_deploy[dirs] = "${S}"
addtask deploy before do_build after do_compile
