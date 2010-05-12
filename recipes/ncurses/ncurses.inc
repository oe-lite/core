DESCRIPTION = "Ncurses library"
HOMEPAGE = "http://www.gnu.org/software/ncurses/ncurses.html"
LICENSE = "MIT"
SECTION = "libs"

PR = "r0"

DEPENDS = "ncurses-native"
DEPENDS_recipe-native = ""
PACKAGES_prepend = "${PN}-tools "
PACKAGES_append = " ${PN}-terminfo"
FILES_${PN}_append = " ${datadir}/tabset"
RPROVIDES_${PN} = "libncurses5${RE}"

inherit autotools

# This keeps only tput/tset in ncurses
# clear/reset are in already busybox
FILES_${PN} = "${bindir}/tput ${bindir}/tset ${libdir}/lib*.so.* /usr/share/tabset /etc/terminfo"
FILES_${PN}-tools = "${bindir}/tic ${bindir}/toe ${bindir}/infotocap ${bindir}/captoinfo ${bindir}/infocmp ${bindir}/clear ${bindir}/reset ${bindir}/tack "
FILES_${PN}-terminfo = "${datadir}/terminfo"
FILES_${PN}-dev += "${bindir}/ncurses5-config"

FILESPATH = "${FILE_DIRNAME}/local:${FILE_DIRNAME}/ncurses-${PV}-${PR}:${FILE_DIRNAME}/ncurses-${PV}:${FILE_DIRNAME}/ncurses:${FILE_DIRNAME}"

EXTRA_OECONF = "--with-shared \
                --with-libtool \
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
	        --with-build-ldflags='' \
	        --with-build-ccflags='' "
export BUILD_CCFLAGS = "-I${S}/ncurses -I${S}/include ${BUILD_CFLAGS}"
export BUILD_LDFLAGS = ""
export EXTRA_OEMAKE = '"BUILD_LDFLAGS=" "BUILD_CCFLAGS=${BUILD_CCFLAGS}"'

# This is necessary so that the "tic" command executed during the install can
# link with the correct libary in staging.
export LD_LIBRARY_PATH = "${STAGING_LIBDIR_NATIVE}"

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

BBCLASSEXTEND = "native sdk"
