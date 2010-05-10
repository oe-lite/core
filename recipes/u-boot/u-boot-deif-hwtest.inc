do_configure_prepend_mpc8313erdb() {
	mv ${S}/include/configs/${UBOOT_MACHINE_HEADER} \
	   ${S}/include/configs/${UBOOT_MACHINE_HEADER}.orig
	sed -e 's%^//#define CONFIG_HWTEST%#define CONFIG_HWTEST%' \
	    -e 's%HRCWH_SW_WATCHDOG_ENABLE%HRCWH_SW_WATCHDOG_DISABLE%' \
	    -e 's%^//#define CONFIG_WATCHDOG%#define CONFIG_WATCHDOG%' \
	    -e 's%^//#define CONFIG_CMD_WDT_TEST%#define CONFIG_CMD_WDT_TEST%' \
	  < ${S}/include/configs/${UBOOT_MACHINE_HEADER}.orig \
	  > ${S}/include/configs/${UBOOT_MACHINE_HEADER}
}

do_configure_prepend() {
	mv ${S}/include/configs/${UBOOT_MACHINE_HEADER} \
	   ${S}/include/configs/${UBOOT_MACHINE_HEADER}.orig
	sed -e 's%^//#define CONFIG_HWTEST%#define CONFIG_HWTEST%' \
	  < ${S}/include/configs/${UBOOT_MACHINE_HEADER}.orig \
	  > ${S}/include/configs/${UBOOT_MACHINE_HEADER}
}