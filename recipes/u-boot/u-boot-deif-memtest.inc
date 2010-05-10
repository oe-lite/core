require u-boot-deif.inc

do_configure_prepend() {
	mv ${S}/include/configs/${UBOOT_MACHINE_HEADER} \
	   ${S}/include/configs/${UBOOT_MACHINE_HEADER}.orig
	sed -e 's%^//#define CONFIG_POST%#define CONFIG_POST%' \
	    -e 's%HRCWH_SW_WATCHDOG_ENABLE%HRCWH_SW_WATCHDOG_DISABLE%' \
	    -e 's%^#define CONFIG_WATCHDOG%//#define CONFIG_WATCHDOG%' \
	  < ${S}/include/configs/${UBOOT_MACHINE_HEADER}.orig \
	  > ${S}/include/configs/${UBOOT_MACHINE_HEADER}
}