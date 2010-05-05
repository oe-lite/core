require linux-deif-${PV}.inc

SRC_URI = "git://dev.doredevelopment.dk/srv/deif/git/linux.git;protocol=ssh;tag=${GIT_TAG}"

S = "${WORKDIR}/git/tools/perf"
DEPENDS = "elfutils binutils"
RDEPENDS = "elfutils binutils"

EXTRA_OEMAKE = "'NO_64BIT=1' 'NO_SVN_TESTS=1' 'NO_PERL=1' 'AR=${AR}' 'CC=${CC}' 'STRIP=${STRIP}' 'CFLAGS=${CFLAGS}' 'prefix='"

do_install() {
    oe_runmake install DESTDIR=${D}
}
