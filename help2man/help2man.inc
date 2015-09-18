# -*- mode:python; -*-
RECIPE_TYPES = "native"

EXTRA_AUTORECONF="-Iaclocal.m4"
inherit autotools-autoreconf

require conf/fetch/gnu.conf
SRC_URI += "${GNU_MIRROR}/${PN}/${PN}-${PV}.tar.xz"

