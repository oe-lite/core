DESCRIPTION = "The GNU Readline library provides a set of functions for use by applications that allow users to edit command lines as they are typed in. Both Emacs and vi editing modes are available. The Readline library includes additional functions to maintain a list of previously-entered command lines, to recall and perhaps reedit those lines, and perform csh-like history expansion on previous commands."
SECTION = "libs"
PRIORITY = "optional"
LICENSE = "GPLv2"

PR = "r0"

DEPENDS = "ncurses${RE}-dev"
RPROVIDES_${PN} += "readline${RE}"

SRC_URI = "\
  ftp://ftp.gnu.org/gnu/readline/readline-${PV}.tar.gz \
"
S = "${WORKDIR}/readline-${PV}"

inherit autotools

BBCLASSEXTEND = "native sdk"
