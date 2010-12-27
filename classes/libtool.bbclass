LIBTOOL_DEPENDS = "${HOST_ARCH}/libtool"
LIBTOOL_DEPENDS_recipe-native = "libtool-native"
LIBTOOL_DEPENDS_cross = "${TARGET_ARCH}/libtool"
LIBTOOL_DEPENDS_sdk-cross = "${TARGET_ARCH}/libtool"
LIBTOOL_DEPENDS_canadian-cross = "${HOST_ARCH}/libtool ${TARGET_ARCH}/libtool"
CLASS_DEPENDS += "${LIBTOOL_DEPENDS}"

# Libtool commands
BUILD_LIBTOOL	= "${BUILD_PREFIX}libtool"
HOST_LIBTOOL	= "${HOST_PREFIX}libtool"
TARGET_LIBTOOL	= "${TARGET_PREFIX}libtool"
LIBTOOL		= "${HOST_LIBTOOL}"
#export LIBTOOL

LIBTOOL_NATIVE_SCRIPTS				= ""
LIBTOOL_HOST_SCRIPTS				= "libtool"
LIBTOOL_TARGET_SCRIPTS				= ""

LIBTOOL_NATIVE_SCRIPTS_recipe-native		= "libtool"
LIBTOOL_HOST_SCRIPTS_recipe-native		= ""

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

LIBTOOL_FIXUP_SEARCH_DIRS = "${D}${libdir} ${D}${base_libdirs}"
LIBTOOL_FIXUP_STRIP_DIRS  = "${D} ${S} ${STAGE_DDIR}"
STAGE_DDIR = "${TARGET_SYSROOT}"
STAGE_DDIR_recipe-native = "${STAGE_DIR}/native"

# FIXME: figure out how to handle canadian-cross here...

libtool_lafile_fixup[dirs] = "${D}"
python libtool_lafile_fixup () {
    import glob, sys, os

    la_files = []
    for la_dir in d.getVar("LIBTOOL_FIXUP_SEARCH_DIRS", True).split():
        la_files += glob.glob("%s/*.la"%(la_dir))

    strip_dirs = set()
    for strip_dir in d.getVar("LIBTOOL_FIXUP_STRIP_DIRS", True).split():
        strip_dirs.add(strip_dir)
        strip_dirs.add(os.path.realpath(strip_dir))

    for filename in la_files:
        fixed = ""
        with open(filename) as la_file:
            for line in la_file.readlines(): 
                #print "line: %s"%(repr(line))
                #line = line.replace("installed=yes", "installed=no")
                for strip_dir in strip_dirs:
                    line = line.replace("-L" + strip_dir, "-L")
                #print "fixed line: %s"%(repr(line))
                fixed += line
        with open(filename, "w") as la_file:
            la_file.write(fixed)
}
