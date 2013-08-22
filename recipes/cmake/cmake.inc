RECIPE_TYPES = "native"

inherit c c++ make
SRC_URI = "http://www.cmake.org/files/v2.8/cmake-${PV}.tar.gz"

PARALLEL_CMAKE = "${@['','--parallel='+d.get('PARALLEL_MAKE').replace('-j','').strip()][int(bool(d.get('PARALLEL_MAKE')))]}"

do_configure() {
	./configure --prefix=/ --no-system-libs ${PARALLEL_CMAKE}
}

FILES_${PN} += "${bindir}/* ${datadir}"
FILES_${PN}-doc += "${docdir}/* ${mandir}/* /doc/* /man/*"
FILES_${PN}-dbg += "${bindir}/.debug/*"

DEPENDS_${PN} += "libgcc libncurses"
