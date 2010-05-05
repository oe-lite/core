inherit ubifs_images

# remember to bump deif-<name>-image INC_PR also!
PR = "r1.${INC_PR}"

# Incremental PR - bump this when kernel (linux-deif) is changed to
# rebuild with new kernel modules.
INC_PR = "1"

RDEPENDS = "\
	busybox busybox-hwclock busybox-mdev busybox-syslogd \
	busybox-inetd \
	busybox-ntpd \
	busybox-shutdown \
	base-passwd \
	mtd-utils \
	dropbear \
	memtester \
	linux-deif-modules \
	netbase \
	performance-test-suite \
	dupdate \
        net-tools-mii \
	ethercat \
	"


#	gdbserver \
#	linux-perf-tool \
#	deif-u-boot-setenv \
