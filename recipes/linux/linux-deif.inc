require linux-deif-common.inc

do_install_append () {
	install -d ${D}${sysconfdir}/init.d
	install -d ${D}${sysconfdir}/rcS.d/
	install -m 0755 ${WORKDIR}/kernel-modules ${D}${sysconfdir}/init.d/
	ln -s ../init.d/kernel-modules ${D}${sysconfdir}/rcS.d/S11kernel-modules
}

SRC_URI += "file://kernel-modules"
FILES_${PN}-modules = "${sysconfdir}/init.d/kernel-modules ${sysconfdir}/rcS.d/S11kernel-modules"

PACKAGES += "${PN}-modules ${PN}"

# kernel modules
PACKAGES += "\
kernel-module-i2c \
kernel-module-mmc-test \
kernel-module-mmc \
kernel-module-mtd-test \
kernel-module-mtd \
kernel-module-rtc \
kernel-module-spi \
kernel-module-fs \
kernel-module-extra \
"
FILES_kernel-module-i2c = "${base_libdir}/modules/${PV}/kernel/drivers/i2c"
FILES_kernel-module-mmc = "${base_libdir}/modules/${PV}/kernel/drivers/mmc"
FILES_kernel-module-mmc-test = "${base_libdir}/modules/${PV}/kernel/drivers/mmc/card/mmc_test.ko"
FILES_kernel-module-mtd = "${base_libdir}/modules/${PV}/kernel/drivers/mtd"
FILES_kernel-module-mtd-test = "${base_libdir}/modules/${PV}/kernel/drivers/mtd/tests"
FILES_kernel-module-rtc = "${base_libdir}/modules/${PV}/kernel/drivers/rtc"
FILES_kernel-module-spi = "${base_libdir}/modules/${PV}/kernel/drivers/spi"
FILES_kernel-module-fs = "${base_libdir}/modules/${PV}/kernel/fs"
FILES_kernel-module-extra = "${base_libdir}/modules/${PV}/kernel"
# END kernel modules

RDEPENDS_${PN}-modules = "\
kernel-module-i2c \
kernel-module-mmc \
kernel-module-mtd \
kernel-module-rtc \
kernel-module-spi \
kernel-module-fs \
"
