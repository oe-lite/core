addtask rstage after do_patch before do_compile
addtask deploy after do_fixup before do_build

IMAGE_BASENAME ?= "${PN}"
IMAGE_FULLNAME ?= "${IMAGE_BASENAME}-${DATETIME}"

IMAGE_PREPROCESS_FUNCS	?= ""
IMAGE_CREATE_FUNCS	?= ""

SRC_URI = ""

FILES_${PN} = ""

# FIXME: do_compile could be renamed to do_build when do_build is
# renamed to do_all, which should be done when merging in BitBake code
# into OE-lite Bakery as bblib.  But on the other hand, this would
# impact most recipes (those messing with do_compile(), so let's just
# stick with do_compile

# IMAGE_PREPROCESS_FUNCS could create device nodes, merge crontab
# entries, mdev.conf and ineted.conf files

do_compile[dirs] = "${IMAGE_DIR}"
do_compile[cleandirs] = "${IMAGE_DIR}"

fakeroot do_compile () {
    echo LD_LIBRARY_PATH=$LD_LIBRARY_PATH
    cp -a ${RSTAGE_DIR}/. ./
    for func in ${IMAGE_PREPROCESS_FUNCS}; do
        $func
    done
    for func in ${IMAGE_CREATE_FUNCS}; do
        $func
    done
}

do_install () {
    :
}

do_deploy[dirs] = "${IMAGE_DEPLOY_DIR}"
do_deploy() {
    :
}

do_rstage[cleandirs]	= "${RSTAGE_DIR}"
do_rstage[dirs]		= "${RSTAGE_DIR}"
do_rstage[recrdeptask]	= "do_package"

do_rstage[import] = "set_stage"
def do_rstage(d):
    if d.get("RECIPE_TYPE") == "canadian-cross":
        def get_dstdir(cwd, package):
            if package.type == "machine":
                return os.path.join(package.arch, "sysroot")
            else:
                return cwd
    else:
        def get_dstdir(cwd, package):
            return cwd
    retval = set_stage(d, "__rstage", "RSTAGE_FIXUP_FUNCS", get_dstdir)
    metadir = d.getVar("metadir", True).lstrip("/")
    if os.path.exists(metadir):
        import shutil
        shutil.rmtree(metadir)
    return retval

RSTAGE_FIXUP_FUNCS ?= ""
