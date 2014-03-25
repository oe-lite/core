## Recipe for building make
##
## GNU make utility to maintain groups of programs. For more information, see:
## http://linux.die.net/man/1/make.

DESCRIPTION = "GNU Make determines which pieces of a large program\
 need to be recompiled, and issues commands to recompile them"
LICENSE = "GPLv2"
HOMEPAGE = "http://www.gnu.org/software/make/"

RECIPE_TYPES = "native sdk"

DEPENDS = ""

require conf/fetch/gnu.conf
SRC_URI = "${GNU_MIRROR}/make/make-${PV}.tar.bz2"

inherit autotools

# Local Variables:
# mode: python
# End:
