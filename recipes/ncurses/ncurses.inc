## Recipe for building ncurses.
##
## The ncurses library routines give the user a terminal-independent method of
## updating character screens with reasonable optimization.
## For more information, see:
## http://linux.die.net/man/3/ncurses

DESCRIPTION = "Ncurses library"
HOMEPAGE = "http://www.gnu.org/software/ncurses/ncurses.html"

RECIPE_TYPES = "machine native sdk"

COMPATIBLE_HOST_ARCHS = ".*-linux-gnu.* .*darwin.* .*linux-uclibc.*"

require conf/fetch/gnu.conf
SRC_URI = "${GNU_MIRROR}/ncurses/ncurses-${PV}.tar.gz"

# Recipe build dependencies
DEPENDS = "native:libncurses libm"
DEPENDS:native = "libm"

inherit autotools make-vpath c++

export LTCC="${CC}"
export LTCFLAGS="${CFLAGS}"

EXTRA_OECONF += "\
--with-shared \
--with-libtool=${STAGE_DIR}/${HOST_CROSS}${stage_bindir}/${LIBTOOL} \
--without-profile \
--without-debug \
--enable-rpath \
--enable-echo \
--enable-const \
--without-ada \
--enable-termcap \
--without-cxx-binding \
--with-terminfo-dirs=${sysconfdir}/terminfo:${datadir}/terminfo \
--enable-overwrite \
"

do_install() {
        do_install_make

        ln -sf curses.h ${D}${includedir}/ncurses.h

        # our ncurses has termcap support
        ln -sf libncurses${SOLIBSDEV} ${D}${libdir}/libtermcap${SOLIBSDEV}
        ln -sf libncurses.a ${D}${libdir}/libtermcap.a

        # include some basic terminfo files
        # stolen ;) from gentoo and modified a bit
        for x in ansi console dumb linux rxvt screen sun vt{52,100,102,200,220} xterm-color xterm-xfree86
        do
                local termfile="$(find "${D}${datadir}/terminfo/" -name "$x" 2>/dev/null)"
                local basedir="$(basename $(dirname "$termfile"))"

                if [ -n "$termfile" ]
                then
                        install -d ${D}${sysconfdir}/terminfo/$basedir
                        mv $termfile ${D}${sysconfdir}/terminfo/$basedir/
                        ln -s /etc/terminfo/$basedir/$x \
                                ${D}${datadir}/terminfo/$basedir/$x
                fi
        done
        # i think we can use xterm-color as default xterm
        if [ -e ${D}${sysconfdir}/terminfo/x/xterm-color ]
        then
                ln -sf xterm-color ${D}${sysconfdir}/terminfo/x/xterm
        fi
}


#Remove la file link to very specific builddir
LIBTOOL_FIXUP_STRIP_DIRS  += " -L${B}/lib"

PACKAGES =+ "${PN}-tools ${PN}-terminfo"

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "ncurses form menu panel"
FILES_${PN}-libncurses-dev = "${libdir}/libtermcap.a ${libdir}/libtermcap${SOLIBSDEV}"
PROVIDES_${PN}-libncurses = "libtermcap"
PROVIDES_${PN}-libncurses[qa] = "allow-missing-soname:libtermcap"
PROVIDES_${PN}-libncurses-dev = "libtermcap-dev"

inherit auto-package-utils
AUTO_PACKAGE_UTILS = "captoinfo clear infocmp infotocap ncurses6-config reset tabs tic toe tput tset"
RDEPENDS_${PN}-captoinfo += "${PN}-tic"
RDEPENDS_${PN}-infotocap += "${PN}-tic"
RDEPENDS_${PN}-reset += "${PN}-tset"
AUTO_PACKAGE_UTILS_DEPENDS += "libncurses"
AUTO_PACKAGE_UTILS_RDEPENDS += "libncurses"

# Keep only tput/tset in primary package (clear/reset are already in busybox)
FILES_${PN} = "${datadir}/tabset ${sysconfdir}/terminfo"
RDEPENDS_${PN}-tools += "${AUTO_PACKAGE_UTILS_PROVIDES}"
FILES_${PN}-terminfo = "${datadir}/terminfo ${libdir}/terminfo"
FILES_${PN}-dev += "${bindir}/ncurses6-config"

DEPENDS_${PN} += "libncurses"
DEPENDS_${PN}-dev = ""
DEPENDS_${PN}-tools += "libncurses"

AUTO_PACKAGE_LIBS_DEV_DEPENDS = "${PN}-dev_${PV}"

# Library package build and run-time dependencies
DEPENDS_${PN}-libncurses= "libc"
DEPENDS_${PN}-libform	= "libncurses"
DEPENDS_${PN}-libmenu	= "libncurses"
DEPENDS_${PN}-libpanel	= "libncurses"

# Package run-time dependencies
RDEPENDS_${PN}		= "libncurses"
RDEPENDS_${PN}-tools	= "libncurses ${PN}"

# Local Variables:
# mode: python
# End:
