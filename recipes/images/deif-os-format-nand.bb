DESCRIPTION = "Create update image with images."
LICENSE = "GPLv2"
PR = "r1"

inherit dupdate_images

RDEPENDS = "\
dupdate-format \
"

do_files_install_append() {
    os.system("ln -s format_nand.sh run_update.sh")
}
