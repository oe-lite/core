# -*- mode:python; -*-

RECIPE_TYPES = "native"

inherit c autotools

SRC_URI = "http://ymorin.is-a-geek.org/download/crosstool-ng/crosstool-ng-${PV}.tar.bz2"

# Official fixes
SRC_URI_FIXES_BASE = "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/${PV}/"

FILES_${PN} += "${libdir}/ct-ng-*"
