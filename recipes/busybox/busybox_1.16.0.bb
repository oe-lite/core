require busybox.inc
INC_PR = ".1"

SRC_URI = "http://www.busybox.net/downloads/busybox-${PV}.tar.bz2 \
	   file://tftpd-fix-file-creation-with-bogus-mode.patch;patch=1 \
	  "

# deif defconfig depends on mtd-utils to build
#DEPENDS_append_deif = "mtd-utils"

# DEIF busybox provides simplified module utils
#RPROVIDES += "\
#	module-init-tools \
#	module-init-tools-depmod \
#	module-init-tools-insmod-static \
#	"
#PROVIDES += "\
#	module-init-tools \
#	module-init-tools-depmod \
#	module-init-tools-insmod-static \
#	"

# Let's emulate update-modules to keep legacy recipes happy
do_install_append_deif () {
	echo > ${D}${sbindir}/update-modules << EOT
#!/bin/sh
/sbin/depmod
EOT
}
RPROVIDES += "update-modules"
PROVIDES += "update-modules"
