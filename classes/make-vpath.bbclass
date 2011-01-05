B = "${WORKDIR}/build"
do_configure[cleandirs] = "${B}"

# no need for distclean when B is cleandir'ed
AUTOTOOLS_DISTCLEAN = "0"
