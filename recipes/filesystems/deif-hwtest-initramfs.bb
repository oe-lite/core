# remember to bump deif-hwtest-image INC_PR also!
PR = "r8.${INC_PR}"

# Incremental PR - bump this when kernel (linux-deif) is changed to
# rebuild with new kernel modules.
INC_PR = "13"

IMAGE_INSTALL = "\
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

export IMAGE_BASENAME = "${PN}"
IMAGE_LINGUAS = ""

inherit poky-image

IMAGE_FSTYPES += "cpio"
