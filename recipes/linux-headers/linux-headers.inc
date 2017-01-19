# -*- mode:python; -*-
inherit kernel-headers

RECIPE_TYPES = "machine sdk"

require conf/fetch/kernelorg.conf
SRC_URI = "${KERNELORG_MIRROR}/linux/kernel/v${@'${PV}'.split('.')[0]+'.x'}/linux-${PV}.tar.xz"
S = "${SRCDIR}/linux-${PV}"
INGREDIENTS_SUBDIR = "linux"

DEFAULT_PREFERENCE = "1"
