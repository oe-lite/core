# -*- mode:python; -*-
inherit kernel-headers

RECIPE_TYPES = "machine sdk"

require conf/fetch/kernelorg.conf
SRC_URI = "${KERNELORG_MIRROR}/linux/kernel/v${KERNEL_VERSION_PATCHLEVEL}/linux-${PV}.tar.bz2"
S = "${SRCDIR}/linux-${PV}"
INGREDIENTS_SUBDIR = "linux"

DEFAULT_PREFERENCE = "1"
