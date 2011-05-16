IMAGE_BASENAME ?= "${MACHINE}-${PN}"
IMAGE_FULLNAME ?= "${IMAGE_BASENAME}-${RECIPE_OPTION_dupdate_version}${DATETIME}"

inherit image

DUPDATE_IMAGE_EXT = '.dupdate'

IMAGE_CREATE_FUNCS += "dupdate_image"

dupdate_image() {
	(
	sha256sum * > sha256sum.txt
	tar chf ${B}/${IMAGE_BASENAME}${DUPDATE_IMAGE_EXT} .
	)
}

RECIPE_OPTIONS_append += "dupdate_script dupdate_version"

do_install_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}${DUPDATE_IMAGE_EXT} ${D}/
}

RSTAGE_FIXUP_FUNCS_append_RECIPE_OPTION_dupdate_version += "dupdate_version"
RSTAGE_FIXUP_FUNCS_append_RECIPE_OPTION_dupdate_script += "dupdate_script_symlink"

RSTAGE_FIXUP_FUNCS += "dupdate_flatten_bootdir"
dupdate_flatten_bootdir () {
    if [ -d boot ]; then
	  mv boot/* .
	  rmdir boot
    fi
}
dupdate_flatten_bootdir[dirs] = "${IMAGE_STAGE}"

dupdate_version () {
	echo "${RECIPE_OPTION_dupdate_version}" > VERSION
}
dupdate_version[dirs] = "${IMAGE_STAGE}"

dupdate_script_symlink () {
	script="${RECIPE_OPTION_dupdate_script}"
	if [ "$script" != "run_update.sh" ] ; then
		ln -s $script run_update.sh
	fi
}
dupdate_script_symlink[dirs] = "${IMAGE_STAGE}"

do_deploy_append () {
	install -m 664 ${B}/${IMAGE_BASENAME}${DUPDATE_IMAGE_EXT} \
		${IMAGE_DEPLOY_DIR}/${IMAGE_FULLNAME}${DUPDATE_IMAGE_EXT}
	ln -sf ${IMAGE_FULLNAME}${DUPDATE_IMAGE_EXT} \
		${IMAGE_DEPLOY_DIR}/${IMAGE_BASENAME}${DUPDATE_IMAGE_EXT}
}
