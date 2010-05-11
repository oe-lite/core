require u-boot.inc

DEFAULT_PREFERENCE = "-1"
DEFAULT_PREFERENCE_mpc8313erdb = "1"
DEFAULT_PREFERENCE_awc500pcm = "1"

UBOOT_MACHINE_mpc8313erdb = "MPC8313ERDB_33_config"
UBOOT_MACHINE_awc500pcm = "awc500pcm_config"
UBOOT_MACHINE_HEADER_mpc8313erdb = "MPC8313ERDB.h"
UBOOT_MACHINE_HEADER_awc500pcm = "awc500pcm.h"

SRC_URI = "git://dev.doredevelopment.dk/srv/deif/git/u-boot.git;protocol=ssh;tag=${GIT_TAG} "

S = "${WORKDIR}/git"

do_configure_append() {
	rm -f ${S}/tools/setlocalversion
}