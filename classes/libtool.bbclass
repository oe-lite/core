# -*- mode:python; -*-

LIBTOOL_DEPENDS = "host-cross:libtool target-cross:libtool"
CLASS_DEPENDS += "${LIBTOOL_DEPENDS}"

# Libtool commands
BUILD_LIBTOOL	= "${BUILD_PREFIX}libtool"
HOST_LIBTOOL	= "${HOST_PREFIX}libtool"
TARGET_LIBTOOL	= "${TARGET_PREFIX}libtool"
LIBTOOL		= "${HOST_LIBTOOL}"
#export LIBTOOL

addhook libtool_fixup to post_recipe_parse
def libtool_fixup(d):
    build_arch = d.getVar("BUILD_ARCH", True)
    host_arch = d.getVar("HOST_ARCH", True)
    target_arch = d.getVar("TARGET_ARCH", True)
    if host_arch == build_arch:
        d.setVar("HOST_LIBTOOL", "${BUILD_LIBTOOL}")
    if target_arch == build_arch:
        d.setVar("TARGET_LIBTOOL", "${BUILD_LIBTOOL}")

LIBTOOL_NATIVE_SCRIPTS				= ""
LIBTOOL_HOST_SCRIPTS				= ""
LIBTOOL_TARGET_SCRIPTS				= "libtool"

LIBTOOL_NATIVE_SCRIPTS_recipe-native		= "libtool"
LIBTOOL_TARGET_SCRIPTS_recipe-native		= ""

LIBTOOL_NATIVE_SCRIPT_FIXUP			= "0"
LIBTOOL_HOST_SCRIPT_FIXUP			= "0"
LIBTOOL_TARGET_SCRIPT_FIXUP			= "0"

libtool_script_fixup () {
    oenote libtool_script_fixup

    if [ "${LIBTOOL_NATIVE_SCRIPT_FIXUP}" = "1" ] ; then
        for script in ${LIBTOOL_NATIVE_SCRIPTS} ; do
            if [ -f $script ]; then
                rm -f $script
                ln -s \
                    ${STAGE_DIR}/native${stage_bindir}/libtool \
                    $script
            fi
        done
    fi

    if [ "${LIBTOOL_HOST_SCRIPT_FIXUP}" = "1" ] ; then
        for script in ${LIBTOOL_HOST_SCRIPTS} ; do
            if [ -f $script ]; then
                rm -f $script
                ln -s \
                    ${STAGE_DIR}/cross${stage_bindir}/${HOST_PREFIX}libtool \
                    $script
            fi
        done
    fi

    if [ "${LIBTOOL_TARGET_SCRIPT_FIXUP}" = "1" ] ; then
        for script in ${LIBTOOL_TARGET_SCRIPTS} ; do
            if [ -f $script ]; then
                rm -f $script
                ln -s \
                    ${STAGE_DIR}/cross${stage_bindir}/${TARGET_PREFIX}libtool \
                    $script
            fi
        done
    fi
}

FIXUP_FUNCS += "libtool_lafile_fixup"

LIBTOOL_FIXUP_SEARCH_DIRS = "${D}${libdir} ${D}${base_libdir}"
LIBTOOL_FIXUP_STRIP_DIRS  = "${D} ${S} ${STAGE_DDIR}"
STAGE_DDIR = "${TARGET_SYSROOT}"
STAGE_DDIR_recipe-native = "${STAGE_DIR}/native"

# FIXME: figure out how to handle canadian-cross here...

libtool_lafile_fixup[dirs] = "${D}"
python libtool_lafile_fixup () {
    import glob, sys, os

    lafiles = []
    for la_dir in d.getVar("LIBTOOL_FIXUP_SEARCH_DIRS", True).split():
        lafiles += glob.glob("%s/*.la"%(la_dir))

    strip_dirs = set()
    for strip_dir in d.getVar("LIBTOOL_FIXUP_STRIP_DIRS", True).split():
        strip_dirs.add(strip_dir)
        strip_dirs.add(os.path.realpath(strip_dir))

    import re
    for filename in lafiles:
        with open(filename, "r") as input_file:
            lafile = input_file.read()
        for strip_dir in strip_dirs:
            lafile = re.sub("-L%s"%(strip_dir),
                             "-L", lafile)
            lafile = re.sub("([' ])%s"%(strip_dir),
                             "\g<1>", lafile)
        pattern = re.compile("^installed=no", re.MULTILINE)
        lafile = re.sub(pattern, "installed=yes", lafile)
        with open(filename, "w") as output_file:
            output_file.write(lafile)
}
