fakeroot do_image_build() {
    set -x
    makedevs_files ${FILES_DIR}
    create_image ${FILES_DIR} ${IMAGE_FILE}
    [ -s ${IMAGE_FILE} ] || return 1
}
EXPORT_FUNCTIONS do_image_build
addtask image_build before do_install after do_files_package
do_image_build[dirs] = "${IMAGE_DEPLOY_DIR} ${FILES_DIR}"


python do_image_deploy() {
    bb.note('DEPLOY')
}
EXPORT_FUNCTIONS do_image_deploy
addtask image_deploy after do_image_build
do_image_deploy[dirs] = "${IMAGE_DEPLOY_DIR}"
