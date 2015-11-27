RECIPE_TYPES = "native sdk"

inherit c c++ make
MAJOR = "${@'.'.join(d.get('PV').split('.')[0:2])}"
SRC_URI = "http://www.cmake.org/files/v${MAJOR}/cmake-${PV}.tar.gz"

PARALLEL_CMAKE = "${@['','--parallel='+d.get('PARALLEL_MAKE').replace('-j','').strip()][int(bool(d.get('PARALLEL_MAKE')))]}"

do_configure() {
	CC=${BUILD_CC}
	CXX=${BUILD_CXX}
	./bootstrap --prefix=${prefix} --verbose ${PARALLEL_CMAKE} \
	--system-curl --no-system-expat --no-system-jsoncpp \
	--no-system-bzip2 --no-system-libarchive -- \
	-DCMAKE_C_COMPILER:PATH="${HOST_CC}" \
	-DCMAKE_CXX_COMPILER:PATH="${HOST_CXX}" \
	-DCMAKE_C_FLAGS:STRING="${HOST_CFLAGS}" \
	-DCMAKE_CXX_FLAGS:STRING="${HOST_CXXFLAGS}" \
	-DCMAKE_AR:PATH="${HOST_AR}" \
	-DCMAKE_RANLIB:PATH="${HOST_RANLIB}" \
	-DCMAKE_LIBRARY_PATH:STRING=${STAGE_DIR}/${HOST_TYPE}${libdir} \
	-DCMAKE_INCLUDE_PATH:STRING=${STAGE_DIR}/${HOST_TYPE}${includedir}
}

do_install[prefuncs] += "do_install_sed"
do_install_sed() {
        #TODO: contact upstream about this, seems weird that it ends
	# up using the target cmake when the buildsystem already has
	# a bootstrapped native one
        sed -e 's|bin/cmake|Bootstrap.cmk/cmake|' -i ${S}/Makefile
}

FILES_${PN} += "${bindir}/* ${datadir}"
FILES_${PN}-doc += "${docdir}/* ${mandir}/* /doc/* /man/*"
FILES_${PN}-dbg += "${bindir}/.debug/*"

#TODO: package-qa is complaining about libgcc-s and libtinfo for native
# but none of those exists for native
DEPENDS += "libcurl libcurl-dev libdl libz libz-dev"
DEPENDS_${PN} += "libcurl libdl libgcc libm libncurses libstdc++ libz"
RDEPENDS_${PN} += "libcurl libdl libstdc++ libz"