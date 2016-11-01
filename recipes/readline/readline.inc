DESCRIPTION = "A set of functions for use by applications that allow users to edit command lines as they are typed in. Both Emacs and vi editing modes are available. The Readline library includes additional functions to maintain a list of previously-entered command lines, to recall and perhaps reedit those lines, and perform csh-like history expansion on previous commands."
HOMEPAGE = "http://www.gnu.org/software/readline/"

RECIPE_TYPES = "machine native sdk"

SRC_URI = "ftp://ftp.gnu.org/gnu/readline/readline-${PV}.tar.gz \
           ${TERMCAP_PATCH}"

TERMCAP_PATCH = "file://0000-curses-link.patch"
TERMCAP_PATCH:HOST_LIBC_mingw = ""

inherit autotools make-vpath

#Only used for Aarch64
AUTOCONFDIRS = "/support"

EXTRA_OECONF += "${TERMCAP_OECONF}"
TERMCAP_OECONF = " ac_cv_lib_ncurses_tgetent=yes bash_cv_termcap_lib=libncurses"
TERMCAP_OECONF:HOST_LIBC_mingw = ""

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "readline history"
AUTO_PACKAGE_LIBS_DEPENDS = "libc ${TERMCAP}"
AUTO_PACKAGE_LIBS_RDEPENDS = "libc ${TERMCAP}"
AUTO_PACKAGE_LIBS_DEV_DEPENDS = "${PN}-dev"
AUTO_PACKAGE_LIBS_DEV_RDEPENDS = "${PN}-dev"

LIBRARY_VERSION = "6"

SOLIBS:HOST_LIBC_mingw = "${@d.get('PV').split('.')[0]}.dll"

DEPENDS = "${TERMCAP}"
TERMCAP = "libtermcap"
TERMCAP:HOST_LIBC_mingw = ""
