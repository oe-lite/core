# remember to bump deif-<name>-image INC_PR also!
PR = "r6.${INC_PR}"

# Incremental PR - bump this when kernel (linux-deif) is changed to
# rebuild with new kernel modules.
INC_PR = "1"

IMAGE_INSTALL = "\
	busybox busybox-hwclock busybox-mdev busybox-syslogd \
	busybox-inetd \
	busybox-ntpd \
	busybox-shutdown \
	base-passwd \
	mtd-utils \
	dropbear \
	memtester \
	linux-deif-modules \
	gdbserver \
	netbase \
	performance-test-suite \
	dupdate \
	deif-u-boot-setenv \
	linux-perf-tool \
	ethercat \
        net-tools-mii \
	"

export IMAGE_BASENAME = "${PN}"
IMAGE_LINGUAS = ""

inherit poky-image

IMAGE_FSTYPES += "ubi"
