# -*- mode:python; -*-

RECIPE_ARCH		 = "${MACHINE_ARCH}${MACHINE_OVERRIDE}"
MACHINE_OVERRIDE	?= ""

HOST_TYPE		 = "machine"
TARGET_TYPE		 = "machine"
HOST_CROSS		 = "cross"
TARGET_CROSS		 = "cross"
