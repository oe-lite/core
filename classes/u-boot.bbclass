#RECIPE_ARCH = "${RECIPE_ARCH_MACHINE}"

require conf/u-boot.conf

inherit kernel-arch

# Why bother?  U-Boot will most likely stay broken for parallel builds
PARALLEL_MAKE = ""

EXTRA_OEMAKE = "ARCH=${UBOOT_ARCH} CROSS_COMPILE=${TARGET_PREFIX}"

CFLAGS[unexport]   = "1"
CPPFLAGS[unexport] = "1"
CXXFLAGS[unexport] = "1"
LDFLAGS[unexport]  = "1"

do_configure () {
    oe_runmake ${RECIPE_OPTION_uboot_config}
}

do_compile () {
    oe_runmake u-boot.bin
}

# Support checking the u-boot image size
addtask sizecheck before do_install after do_compile
do_sizecheck () {
}
do_sizecheck_append_RECIPE_OPTION_uboot_maxsize () {
    size=`ls -l ${UBOOT_IMAGE} | awk '{ print $5}'`
    if [ "$size" -ge "${RECIPE_OPTION_uboot_maxsize}" ]; then
	die  "The U-Boot image (size=$size > ${RECIPE_OPTION_uboot_maxsize}) is too big."
    fi
}
do_install () {
    install -d ${D}${bootdir}
    install -m 0644 ${UBOOT_IMAGE} ${D}${bootdir}
}

PACKAGES = "${PN}"
FILES_${PN} = "${bootdir}/${UBOOT_IMAGE_FILENAME}"

addtask deploy before do_build after do_compile
do_deploy[dirs] = "${IMAGE_DEPLOY_DIR} ${S}"

do_deploy () {
    install -m 0644 ${UBOOT_IMAGE} \
	${IMAGE_DEPLOY_DIR}/${UBOOT_IMAGE_DEPLOY_FILE}
    md5sum <${UBOOT_IMAGE} \
	>${IMAGE_DEPLOY_DIR}/${UBOOT_IMAGE_DEPLOY_FILE}.md5

    cd ${IMAGE_DEPLOY_DIR}
    if [ -n "${UBOOT_IMAGE_DEPLOY_LINK}" ] ; then
	rm -f ${UBOOT_IMAGE_DEPLOY_LINK}
	ln -sf ${UBOOT_IMAGE_DEPLOY_FILE} ${UBOOT_IMAGE_DEPLOY_LINK}
    fi
}
