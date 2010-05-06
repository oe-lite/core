inherit cpio_images
# remember to bump deif-os-kernel INC_PR also!
PR = "r1.${INC_PR}"

# Incremental PR - bump this when kernel (linux-deif) is changed to
# rebuild with new kernel modules.
INC_PR = "1"

RDEPENDS = "\
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
	performance-test-suite \
	"

#	ethtool \
#	deif-u-boot-setenv \
#	linux-perf-tool \

