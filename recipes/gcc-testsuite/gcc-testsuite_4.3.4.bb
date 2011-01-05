DESCRIPTION = "GCC testsuite - a collection of compile and runtime tests for GCC."
LICENSE = "GPL"

# Note: Requires DejaGNU test framework installed on host (apt-get install dejagnu).

SRC_URI = "ftp://gcc.gnu.org/pub/gcc/releases/gcc-${PV}/gcc-testsuite-${PV}.tar.gz \
	file://board.exp"

S = "${SRCDIR}/gcc-${PV}"

# DejaGnu configuration
DG_TOOLNAME ?= "gcc"
DG_TARGET_HOSTNAME ?= "127.0.0.1"
DG_TARGET_USERNAME ?= "root"

# Default tests
DG_C_TESTS ?= "compile.exp noncompile.exp"
DG_CXX_TESTS ?= "dg.exp"

do_configure () {
	# Create site configuration
	echo 'lappend boards_dir "."' > site.exp
	echo "set target_alias ${TARGET_SYS}" >> site.exp

	# Create board configuration
	cp ${SRCDIR}/board.exp board.exp
	echo "set_board_info hostname ${DG_TARGET_HOSTNAME}" >> board.exp
	echo "set_board_info username ${DG_TARGET_USERNAME}" >> board.exp
}

DG_RUN_CMD = "runtest --tool ${DG_TOOLNAME} --srcdir ${S}/gcc/testsuite --all --target ${MACHINE_ARCH} GXX_UNDER_TEST=${MACHINE_PREFIX}g++ GCC_UNDER_TEST=${MACHINE_PREFIX}gcc"

do_compile () {
	# Exclude board config when running gcc compile tests
	if [ "${DG_TOOLNAME}" == "gcc" ]
	then
	        ! echo ${DG_RUN_CMD} ${DG_C_TESTS} > /dev/tty
		! ${DG_RUN_CMD} ${DG_C_TESTS} > /dev/tty
	fi
	# Include board config for g++ runtime tests
	if [ "$DG_TOOLNAME" == "g++" ]
	then
	        ! echo ${DG_RUN_CMD} --target_board board ${DG_CXX_TESTS} > /dev/tty
		! ${DG_RUN_CMD} --target_board board ${DG_CXX_TESTS} > /dev/tty
	fi
}

do_install () {
	cp ${DG_TOOLNAME}.log ${TMPDIR}/${MACHINE_ARCH}-${DG_TOOLNAME}-testsuite.log
	cp ${DG_TOOLNAME}.sum ${TMPDIR}/${MACHINE_ARCH}-${DG_TOOLNAME}-testsuite.sum
}
