# -*- mode:python; -*-

C_DEPENDS = "host-cross:ccx"
C_DEPENDS:>canadian-cross = " target-cross:cc"
CLASS_DEPENDS += "${C_DEPENDS}"
