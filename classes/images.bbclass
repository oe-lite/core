DEPENDS_prepend += "makedevs-native"

makedevs_files() {
    for devtable in ${1}/${devtable}/*; do
        makedevs -r ${1} -D $devtable
    done
}

fakeroot do_image_build() {
    set -x
    makedevs_files ${FILES_DIR}
    create_image ${FILES_DIR} ${D}/${IMAGE_FILE}
    [ -s ${D}/${IMAGE_FILE} ] || return 1
}
EXPORT_FUNCTIONS do_image_build
addtask image_build before do_package_install after do_files_fixup
do_image_build[dirs] = "${IMAGE_DEPLOY_DIR} ${FILES_DIR}"


do_image_deploy() {
    cp -f ${D}/${IMAGE_FILE}  ${IMAGE_DEPLOY_DIR}
}
EXPORT_FUNCTIONS do_image_deploy
addtask image_deploy before do_package_install after do_image_build
do_image_deploy[dirs] = "${IMAGE_DEPLOY_DIR}"
