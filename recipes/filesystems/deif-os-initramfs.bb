# remember to bump deif-os-kernel INC_PR also!
PR = "r8.${INC_PR}"

# Incremental PR - bump this when kernel (linux-deif) is changed to
# rebuild with new kernel modules.
INC_PR = "2"

IMAGE_INSTALL = "\
	initramfs-live-boot \
	busybox-os-initramfs \
	busybox-os-initramfs-hwclock \
	busybox-os-initramfs-mdev \
	busybox-os-initramfs-syslogd \
	busybox-os-initramfs-inetd \
	linux-deif-modules \
	base-passwd \
	mtd-utils \
	dropbear dropbear-host-key \
	netbase \
	dupdate \
	deif-u-boot-setenv \
	performance-test-suite \
        ethtool \
	linux-perf-tool \
	"


export IMAGE_BASENAME = "${PN}"
IMAGE_LINGUAS = ""

inherit poky-image

IMAGE_FSTYPES += "cpio"
