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
UBOOT_IMAGE ?= "${PN}-${EPV}-${MACHINE}-${DATETIME}.bin"
UBOOT_SYMLINK ?= "${PN}-${MACHINE}.bin"

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
	install -D ${S}/u-boot.bin ${IMAGE_DEPLOY_DIR}/${UBOOT_IMAGE}
	ln -fs ${UBOOT_IMAGE} ${IMAGE_DEPLOY_DIR}/${UBOOT_SYMLINK}
}
do_deploy[dirs] = "${S}"
addtask deploy before do_package_install after do_install
