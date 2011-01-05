DESCRIPTION = "Ncurses library"
HOMEPAGE = "http://www.gnu.org/software/ncurses/ncurses.html"
LICENSE = "MIT"
SECTION = "libs"

BBCLASSEXTEND = "native sdk"

PACKAGES_prepend =+ "\
${PN}-tools ${PN}-terminfo \
${PN}-libncurses ${PN}-libform ${PN}-libmenu ${PN}-libpanel"

# Recipe build dependencies
DEPENDS = "ncurses-native"
DEPENDS_recipe-native = ""

# Package build dependencies
DEPENDS_${PN}-dev	= "${PN}-libncurses \
	${PN}-libform ${PN}-libmenu ${PN}-libpanel"

# Package build provides
PROVIDES_${PN}-dev	= "libncurses${RE} libncurses5${RE} libtermcap${RE} \
	libform${RE} libmenu${RE} libpanel${RE}"

# Library package build and run-time dependencies
RDEPENDS_${PN}-libform	= "${HOST_ARCH}/sysroot-libdl ${PN}-libncurses"
DEPENDS_${PN}-libform	= "${RDEPENDS_${PN}-libform}"
RDEPENDS_${PN}-libmenu	= "${HOST_ARCH}/sysroot-libdl ${PN}-libncurses"
DEPENDS_${PN}-libmenu	= "${RDEPENDS_${PN}-libmenu}"
RDEPENDS_${PN}-libpanel	= "${HOST_ARCH}/sysroot-libdl ${PN}-libncurses"
DEPENDS_${PN}-libpanel	= "${RDEPENDS_${PN}-libpanel}"

# Package run-time dependencies
RDEPENDS_${PN}		= "${HOST_ARCH}/sysroot-libdl ${PN}-libncurses"
RDEPENDS_${PN}-tools	= "${HOST_ARCH}/sysroot-libdl ${PN}-libncurses ${PN}"

# Package run-time provides
RPROVIDES_${PN}-libncurses	= "libncurses${RE} libncurses5${RE}"
RPROVIDES_${PN}-libform		= "libform{RE}"
RPROVIDES_${PN}-libmenu		= "libmenu{RE}"
RPROVIDES_${PN}-libpanel	= "libpanel{RE}"

require conf/fetch/gnu.conf
SRC_URI = "${GNU_MIRROR}/ncurses/ncurses-${PV}.tar.gz"

inherit autotools c++

export LTCC="${CC}"
export LTCFLAGS="${CFLAGS}"

EXTRA_OECONF += "\
--with-shared \
--with-libtool=`which ${LIBTOOL}` \
--without-profile \
--without-debug \
--disable-rpath \
--enable-echo \
--enable-const \
--without-ada \
--enable-termcap \
--without-cxx-binding \
--with-terminfo-dirs=${sysconfdir}/terminfo:${datadir}/terminfo \
--enable-overwrite \
"

# This is necessary so that the "tic" command executed during the install can
# link with the correct libary in staging.
#export LD_LIBRARY_PATH = "${STAGING_LIBDIR_NATIVE}"

do_install() {
	autotools_do_install

	ln -sf curses.h ${D}${includedir}/ncurses.h

	# our ncurses has termcap support
	ln -sf libncurses.so ${D}${libdir}/libtermcap.so
	ln -sf libncurses.a ${D}${libdir}/libtermcap.a

	# include some basic terminfo files
	# stolen ;) from gentoo and modified a bit
	for x in ansi console dumb linux rxvt screen sun vt{52,100,102,200,220} xterm-color xterm-xfree86
        do
                local termfile="$(find "${D}${datadir}/terminfo/" -name "${x}" 2>/dev/null)"
                local basedir="$(basename $(dirname "${termfile}"))"

                if [ -n "${termfile}" ]
                then
                        install -d ${D}${sysconfdir}/terminfo/${basedir}
                        mv ${termfile} ${D}${sysconfdir}/terminfo/${basedir}/
                        ln -s /etc/terminfo/${basedir}/${x} \
                                ${D}${datadir}/terminfo/${basedir}/${x}
                fi
        done
	# i think we can use xterm-color as default xterm
	if [ -e ${D}${sysconfdir}/terminfo/x/xterm-color ]
	then
		ln -sf xterm-color ${D}${sysconfdir}/terminfo/x/xterm
	fi
}

FILES_${PN}_append = " ${datadir}/tabset"

# Keep only tput/tset in primary package (clear/reset are already in busybox)
FILES_${PN} = "${bindir}/tput ${bindir}/tset ${datadir}/tabset ${sysconfdir}/terminfo"
FILES_${PN}-tools = "${bindir}/tic ${bindir}/toe ${bindir}/infotocap ${bindir}/captoinfo ${bindir}/infocmp ${bindir}/clear ${bindir}/reset ${bindir}/tack "
FILES_${PN}-terminfo = "${datadir}/terminfo"
FILES_${PN}-dev += "${bindir}/ncurses5-config"
FILES_${PN}-libncurses = "${libdir}/libncurses${SOLIBS}"
FILES_${PN}-libform = "${libdir}/libform${SOLIBS}"
FILES_${PN}-libmenu = "${libdir}/libmenu${SOLIBS}"
FILES_${PN}-libpanel = "${libdir}/libpanel${SOLIBS}"
