inherit tar-image

IMAGE_BASENAME = "${PN}"

RECIPE_ARCH = "${RECIPE_ARCH_MACHINE}"

RECIPE_OPTIONS += "rootfs_name"
DEFAULT_CONFIG_rootfs_name = "base-rootfs"
DEPENDS += "${RECIPE_OPTION_rootfs_name}"

addtask image_qa_prep before do_image_qa after do_stage_fixup
do_image_qa_prep[dirs] = "${WORKDIR}/image-qa"
do_image_qa_prep[cleandirs] = "${WORKDIR}/image-qa"
fakeroot do_image_qa_prep () {
    tar xfz ${TARGET_SYSROOT}/${RECIPE_OPTION_rootfs_name}.tar.gz
}

inherit image-qa
IMAGE_QA_HOST_READELF_LIB_DIRS += "${WORKDIR}/image-qa/${RECIPE_OPTION_rootfs_name}${base_libdir} ${WORKDIR}/image-qa/${RECIPE_OPTION_rootfs_name}${libdir}"
