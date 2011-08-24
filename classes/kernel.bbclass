DESCRIPTION ?= "Linux kernel"
LICENSE ?= "GPL"

#RECIPE_ARCH = "${RECIPE_ARCH_MACHINE}"

require conf/kernel.conf

inherit kernel-common kernel-modules-strip

EXTRA_OEMAKE += "CROSS_COMPILE=${TARGET_PREFIX}"

RECIPE_OPTIONS += "kernel_defconfig"
DEFCONFIG_FILE ?= "${SRCDIR}/defconfig"
DEFCONFIG = "${@d.getVar('RECIPE_OPTION_kernel_defconfig', 1) or ''}"

kernel_do_configure () {
    if [ -e "${DEFCONFIG_FILE}" ]; then
	cp "${DEFCONFIG_FILE}" "${S}/.config"
	yes '' | oe_runmake oldconfig
    else
	if [ -n "${DEFCONFIG}" ] ; then
	    oe_runmake ${DEFCONFIG}
	else
	    die "No default configuration for ${MACHINE} available."
	fi
    fi
}

do_configure () {
    kernel_do_configure
}

#do_menuconfig() {
#    export TERMWINDOWTITLE="${PN} Kernel Configuration"
#    export SHELLCMDS="make menuconfig"
#    ${TERMCMDRUN}
#    if [ $? -ne 0 ]; then
#        echo "Fatal: '${TERMCMD}' not found. Check TERMCMD variable."
#        exit 1
#    fi
#}
#do_menuconfig[nostamp] = "1"
#addtask menuconfig after do_patch

kernel_do_compile () {
    if [ -n "${BUILD_TAG}" ]; then
        export KBUILD_BUILD_VERSION="${BUILD_TAG}"
    fi

    oe_runmake include/linux/version.h
    oe_runmake ${RECIPE_OPTION_kernel_imagetype}

    if (grep -q -i -e '^CONFIG_MODULES=y$' .config); then
	oe_runmake modules
    else
	oenote "no modules to compile"
    fi

    # Check if scripts/genksyms exists and if so, build it
    if [ -e scripts/genksyms/ ]; then
	oe_runmake SUBDIRS="scripts/genksyms"
    fi
}

do_compile () {
    kernel_do_compile
}

KERNEL_UIMAGE_DEPENDS = "${@['', 'u-boot-tools-native-mkimage']['${RECIPE_OPTION_kernel_imagetype}' == 'uImage']}"
DEPENDS += "${KERNEL_UIMAGE_DEPENDS}"

RECIPE_OPTIONS += "kernel_uimage \
    kernel_uimage_entrypoint kernel_uimage_loadaddress kernel_uimage_name"
KERNEL_UIMAGE_DEPENDS_RECIPE_OPTION_kernel_uimage = "u-boot-mkimage-native"
DEPENDS += "${KERNEL_UIMAGE_DEPENDS}"
DEFAULT_CONFIG_kernel_uimage = "0"
DEFAULT_CONFIG_kernel_uimage_entrypoint = "20008000"
DEFAULT_CONFIG_kernel_uimage_loadaddress = "${RECIPE_OPTION_kernel_uimage_entrypoint}"
DEFAULT_CONFIG_kernel_uimage_name = "${DISTRO}/${PV}/${MACHINE}"

kernel_do_compile_append_RECIPE_OPTION_kernel_uimage () {
    ENTRYPOINT=${RECIPE_OPTION_kernel_uimage_entrypoint}
    if [ -n "$UBOOT_ENTRYSYMBOL" ] ; then
	ENTRYPOINT=`${HOST_PREFIX}nm ${S}/vmlinux | \
	    awk '$3=="${RECIPE_OPTION_kernel_uimage_entrypoint}" {print $1}'`
    fi

    if [ -e "arch/${KERNEL_ARCH}/boot/compressed/vmlinux" ] ; then
	${OBJCOPY} -O binary -R .note -R .note.gnu.build-id -R .comment -S \
	arch/${KERNEL_ARCH}/boot/compressed/vmlinux linux.bin
	mkimage -A ${UBOOT_ARCH} -O linux -T kernel -C none \
	-a ${RECIPE_OPTION_kernel_uimage_loadaddress} \
	-e $ENTRYPOINT \
	-n ${RECIPE_OPTION_kernel_uimage_name} \
	-d linux.bin arch/${KERNEL_ARCH}/boot/uImage
	rm -f linux.bin
    else
	${OBJCOPY} -O binary -R .note -R .note.gnu.build-id -R .comment -S \
        vmlinux linux.bin
	rm -f linux.bin.gz
	gzip -9 linux.bin
	mkimage -A ${UBOOT_ARCH} -O linux -T kernel -C gzip \
	-a ${RECIPE_OPTION_kernel_uimage_loadaddress} \
	-e $ENTRYPOINT \
	-n ${RECIPE_OPTION_kernel_uimage_name} \
	-d linux.bin.gz arch/${KERNEL_ARCH}/boot/uImage
	rm -f linux.bin.gz
    fi
}

UIMAGE_KERNEL_OUTPUT = ""
UIMAGE_KERNEL_OUTPUT_append_RECIPE_OPTION_kernel_uimage = "arch/${KERNEL_ARCH}/boot/uImage"
KERNEL_OUTPUT += "${UIMAGE_KERNEL_OUTPUT}"

RECIPE_OPTIONS += "kernel_dtb kernel_dtc kernel_dtc_flags kernel_dtc_source"
DEFAULT_CONFIG_kernel_dtc_flags = "-R 8 -p 0x3000"
DEFAULT_CONFIG_kernel_dtc_source = "arch/${KERNEL_ARCH}/boot/dts/${MACHINE}.dts"

python () {
    kernel_dtc = d.getVar('RECIPE_OPTION_kernel_dtc', True)
    kernel_dtb = d.getVar('RECIPE_OPTION_kernel_dtb', True)
    if kernel_dtc and kernel_dtc != 0:
	kernel_dtc_source = d.getVar('RECIPE_OPTION_kernel_dtc_source', True)
	dts = os.path.basename(kernel_dtc_source)
	(dts_name, dts_ext) = os.path.splitext(dts)
	if dts_ext != '.dts':
	    dts_name = dts
	d.setVar('KERNEL_DEVICETREE', dts_name + ".dtb")
    elif kernel_dtb:
	d.setVar('KERNEL_DEVICETREE', kernel_dtb)
    else:
	d.setVar('KERNEL_DEVICETREE', '')
}

kernel_do_compile_append_RECIPE_OPTION_kernel_dtc () {
    scripts/dtc/dtc -I dts -O dtb ${RECIPE_OPTION_kernel_dtc_flags} \
	-o ${KERNEL_DEVICETREE} ${RECIPE_OPTION_kernel_dtc_source}
}

kernel_do_install () {
    install -d ${D}${bootdir}
    install -m 0644 ${KERNEL_IMAGE} ${D}${bootdir}/${KERNEL_IMAGE_FILENAME}
    install -m 0644 .config ${D}${bootdir}/config

    if [ -n "${KERNEL_DEVICETREE}" ] ; then
	install -m 0644 ${KERNEL_DEVICETREE} ${D}${bootdir}/${KERNEL_DEVICETREE_FILENAME}
    fi

    if (grep -q -i -e '^CONFIG_MODULES=y$' .config); then
	oe_runmake DEPMOD=echo INSTALL_MOD_PATH="${D}" modules_install
	rm ${D}/lib/modules/*/build ${D}/lib/modules/*/source
    else
	oenote "no modules to install"
    fi

    install -d ${D}${bootdir}
    for kernel_output in ${KERNEL_OUTPUT} ; do
	install -m 0644 ${kernel_output} ${D}${bootdir}/
    done

    install -d ${D}/kernel
    cp -fR scripts ${D}/kernel/
    cp -fR include ${D}/kernel/
    cp -fR Makefile ${D}/kernel
    cp -fR .config ${D}/kernel
    mkdir -p ${D}/kernel/arch/${KERNEL_ARCH}
    cp -fR arch/${KERNEL_ARCH}/lib ${D}/kernel/arch/${KERNEL_ARCH}
    cp -fR arch/${KERNEL_ARCH}/include ${D}/kernel/arch/${KERNEL_ARCH}
    cp -fR arch/${KERNEL_ARCH}/Makefile ${D}/kernel/arch/${KERNEL_ARCH}


    install_kernel_headers
}

INSTALL_HDR_PATH ?= "${D}${includedir}/.."

install_kernel_headers () {
    mkdir -p ${D}${includedir}
    oe_runmake INSTALL_HDR_PATH="${INSTALL_HDR_PATH}" headers_install
}

do_install () {
    kernel_do_install
}

PACKAGES = "${PN} ${PN}-vmlinux ${PN}-dev ${PN}-headers ${PN}-modules ${PN}-dtb ${PN}-kernel-headers"

FILES_${PN} = "${bootdir}/${KERNEL_IMAGE_FILENAME}"
FILES_${PN}-dtb = "${bootdir}/${KERNEL_DEVICETREE_FILENAME}"
FILES_${PN}-vmlinux = "${bootdir}/vmlinux"
FILES_${PN}-dev = "${bootdir}/System.map ${bootdir}/Module.symvers \
    ${bootdir}/config"
FILES_${PN}-headers = "${includedir}"
FILES_${PN}-modules = "/lib/modules"
FILES_${PN}-kernel-headers = "kernel"
PROVIDES_${PN} = "kernel"

# FIXME: implement auto-package-kernel-modules.bbclass to split out
# modules into separate packages

# Support checking the kernel size since some kernels need to reside
# in partitions with a fixed length or there is a limit in
# transferring the kernel to memory
inherit sizecheck
KERNEL_SIZECHECK = ""
KERNEL_SIZECHECK_append_RECIPE_OPTION_kernel_maxsize = "${KERNEL_IMAGE}:${RECIPE_OPTION_kernel_maxsize}"
SIZECHECK += "${KERNEL_SIZECHECK}"

addtask deploy after do_fixup before do_build
do_deploy[dirs] = "${IMAGE_DEPLOY_DIR} ${S}"

do_deploy() {
    install -m 0644 ${KERNEL_IMAGE} \
	${IMAGE_DEPLOY_DIR}/${KERNEL_IMAGE_DEPLOY_FILE}
    md5sum <${KERNEL_IMAGE} \
	>${IMAGE_DEPLOY_DIR}/${KERNEL_IMAGE_DEPLOY_FILE}.md5

    if [ -n "${KERNEL_DEVICETREE}" ] ; then
	install -m 0644 "${KERNEL_DEVICETREE}" \
	    ${IMAGE_DEPLOY_DIR}/${KERNEL_DEVICETREE_DEPLOY_FILE}
	md5sum <"${KERNEL_DEVICETREE}" \
	    >${IMAGE_DEPLOY_DIR}/${KERNEL_DEVICETREE_DEPLOY_FILE}.md5
    fi

    cd ${IMAGE_DEPLOY_DIR}
    if [ -n "${KERNEL_IMAGE_DEPLOY_LINK}" ] ; then
	for ext in "" ".md5"; do
	    rm -f  ${KERNEL_IMAGE_DEPLOY_LINK}$ext
	    ln -sf ${KERNEL_IMAGE_DEPLOY_FILE}$ext \
		   ${KERNEL_IMAGE_DEPLOY_LINK}$ext
	done
    fi
    if [ -n "${KERNEL_DEVICETREE}" -a \
	 -n "${KERNEL_DEVICETREE_DEPLOY_LINK}" ] ; then
	for ext in "" ".md5"; do
	    rm -f  ${KERNEL_DEVICETREE_DEPLOY_LINK}$ext
	    ln -sf ${KERNEL_DEVICETREE_DEPLOY_FILE}$ext \
		   ${KERNEL_DEVICETREE_DEPLOY_LINK}$ext
	done
    fi
}
