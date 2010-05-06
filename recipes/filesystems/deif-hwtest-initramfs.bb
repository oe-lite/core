inherit cpio_images
# remember to bump deif-hwtest-image INC_PR also!
PR = "r1.${INC_PR}"

# Incremental PR - bump this when kernel (linux-deif) is changed to
# rebuild with new kernel modules.
INC_PR = "1"

RDEPENDS = "\
	busybox-hwtest-initramfs \
	busybox-hwtest-initramfs-hwclock \
	busybox-hwtest-initramfs-mdev \
	base-passwd \
	mtd-utils \
	dropbear dropbear-host-key \
	memtester \
	mempattern \
	linux-deif-modules \
	kernel-module-mtd-speedtest \
	kernel-module-mtd-stresstest \
	kernel-module-mtd-readtest \
	kernel-module-mtd-pagetest \
	kernel-module-mtd-oobtest \
	kernel-module-mtd-subpagetest \
	kernel-module-mtd-torturetest \
	kernel-module-mtd-pattern \
	kernel-module-mmc-test \
	netbase \
	dupdate \
	deif-u-boot-setenv \
	ethercat \
        ethtool \
        net-tools-mii \
	"
