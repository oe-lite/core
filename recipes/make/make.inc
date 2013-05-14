DESCRIPTION = "GNU Make determines which pieces of a large program\
 need to be recompiled, and issues commands to recompile them"
LICENSE = "GPLv2"
HOMEPAGE = "http://www.gnu.org/software/make/"

RECIPE_TYPES = "native"

DEPENDS = ""

require conf/fetch/gnu.conf
SRC_URI = "${GNU_MIRROR}/make/make-${PV}.tar.bz2"

inherit autotools

DEPENDS_${PN} = "native:binutils native:gettext"
RDEPENDS_${PN} = "native:binutils"
