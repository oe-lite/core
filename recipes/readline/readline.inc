DESCRIPTION = "A set of functions for use by applications that allow users to edit command lines as they are typed in. Both Emacs and vi editing modes are available. The Readline library includes additional functions to maintain a list of previously-entered command lines, to recall and perhaps reedit those lines, and perform csh-like history expansion on previous commands."
HOMEPAGE = "http://www.gnu.org/software/readline/"

RECIPE_TYPES = "machine native sdk"

SRC_URI = "ftp://ftp.gnu.org/gnu/readline/readline-${PV}.tar.gz"

inherit autotools make-vpath

inherit auto-package-libs
AUTO_PACKAGE_LIBS = "readline history"
AUTO_PACKAGE_LIBS_DEV_DEPENDS = "${PN}-dev"

DEPENDS = "libtermcap"
DEPENDS:HOST_OS_mingw32 = ""
