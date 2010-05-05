SECTION = "console/utils"
DESCRIPTION = "Collection of simple performance utils for benchmarking cpu, memory, and file I/O."
LICENSE = "GPLv2"

# to upgrade, change SRCREV and bump PR
PR = "r4"
SRCREV = "2dd242f9b6070834648ead16068cd20deae41ffb"

SRC_URI = "git://git.doredevelopment.dk/performance-test-suite.git;protocol=git"
S = "${WORKDIR}/git"

#No optimization
CFLAGS = ""

do_compile () {
	oe_runmake
}

do_install () {
	install -d ${D}${bindir}
	install -m 0755 cpu-timedload/cpu-timedload ${D}${bindir}/
	install -m 0755 cpu-benchmark/cpu-benchmark ${D}${bindir}/
	install -m 0755 memory-benchmark/memory-benchmark ${D}${bindir}/
	install -m 0755 file-benchmark/file-benchmark ${D}${bindir}/
}
