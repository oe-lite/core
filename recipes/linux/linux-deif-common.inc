DESCRIPTION = "DEIF BSP Linux Kernel"
SECTION = "kernel"
AUTHOR = "Esben Haabendal <eha@doredevelopment.dk>"
HOMEPAGE = "https://dev.doredevelopment.dk/deif/wiki/Linux"
LICENSE = "GPL"

KERNEL_IMAGETYPE = "uImage"
KERNEL_IMAGETYPE_mpc8313erdb = "uImage.lzma"
INHIBIT_KERNEL_UIMAGE_OVERRIDE = "1"
DEPENDS += "u-boot-mkimage-native"
inherit kernel
KERNEL_MAJOR_VERSION = "2.6"
KERNEL_VERSION = "${PV}-${PR}"

DEFAULT_PREFERENCE = "-1"
DEFAULT_PREFERENCE_mpc8313erdb ?= "1"
DEFAULT_PREFERENCE_awc500pcm ?= "1"

SRC_URI = "git://dev.doredevelopment.dk/srv/deif/git/linux.git;protocol=ssh;tag=${GIT_TAG}"

S = "${WORKDIR}/git"

FILESPATH = "${@base_set_filespath([ "${FILE_DIRNAME}/${PF}", "${FILE_DIRNAME}/${P}", "${FILE_DIRNAME}/${PN}", "${FILE_DIRNAME}/linux-deif-${PV}", "${FILE_DIRNAME}/linux-${PV}", "${FILE_DIRNAME}/files", "${FILE_DIRNAME}" ], d)}"

DEFCONFIG = ""
DEFCONFIG_mpc8313erdb = "83xx/mpc8313_rdb_defconfig"
DEFCONFIG_awc500pcm = "83xx/awc500pcm_defconfig"

do_configure[dirs] = "${S}"
do_configure() {
	if [ ! -e ${WORKDIR}/defconfig ]; then
		if [ -n "${DEFCONFIG}" ] ; then
			yes '' | oe_runmake ${DEFCONFIG}
		else
			die "No default configuration for ${MACHINE} available."
		fi
	else
		cp ${WORKDIR}/defconfig ${S}/.config
		yes '' | oe_runmake oldconfig
	fi

	mv ${S}/.config tmp-dot-config
	sed -e 's/CONFIG_LOCALVERSION_AUTO=y/CONFIG_LOCALVERSION_AUTO=n/' \
	    -e '/CONFIG_INITRAMFS_SOURCE/d' \
	    < tmp-dot-config > ${S}/.config
	rm tmp-dot-config
	yes '' | oe_runmake oldconfig
}
