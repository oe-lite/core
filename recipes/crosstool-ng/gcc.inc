# -*- mode:python; -*-

FILESPATHPKG = "${P}:${PN}-${@'.'.join('${PV}'.split('.')[:2])}:${PN}:files"

require gcc-versions.inc

B = "${WORKDIR}/build"

# Depend on the right version of the ct-ng tool
DEPENDS := "native:crosstool-ng_${PV}"

RECIPE_FLAGS += "extra_toolchain_patch"
EXTRA_TOOLCHAIN_DEPENDS = ""
EXTRA_TOOLCHAIN_DEPENDS:USE_extra_toolchain_patch = "${USE_extra_toolchain_patch}"
# Why don't we add this to the internal cross toolchain?
#DEPENDS:>cross = " ${EXTRA_TOOLCHAIN_DEPENDS}"
DEPENDS:>machine = " ${EXTRA_TOOLCHAIN_DEPENDS}"
DEPENDS:>canadian-cross = " ${EXTRA_TOOLCHAIN_DEPENDS}"

TUI_DEPENDS				= "host:libtermcap host:libreadline"
TUI_DEPENDS:HOST_OS_mingw32		= ""
DEPENDS:>machine			+= " ${TUI_DEPENDS}"
DEPENDS:>sdk				+= " ${TUI_DEPENDS}"
DEPENDS:>canadian-cross			+= " ${TUI_DEPENDS} host:libexpat"

# FIXME: allow machine/sdk/canadian-cross toolchains to be built
# statically, to make it more robust against host machine differences

# FIXME: this looks REALLY wrong!
BUILD_DEPENDS_CANADIAN = "host:libdl target:libdl target:libpthread target:libm"
BUILD_DEPENDS_CANADIAN:HOST_OS_mingw32 = "target:libdl target:libpthread target:libm"
DEPENDS:>canadian-cross += " ${BUILD_DEPENDS_CANADIAN}"

DEPENDS += "${TOOLCHAIN_DEPENDS}"
TOOLCHAIN_DEPENDS = ""
addhook gcc_depends_fixup to post_recipe_parse
def gcc_depends_fixup(d):
    if (d.getVar("RECIPE_TYPE", True) == "cross" and
        d.getVar("MACHINE_CT_KERNEL_VERSION", True) == "custom"):
        d.setVar("TOOLCHAIN_DEPENDS", "target:linux-headers")

require gcc-fetch.inc
require gcc-configure.inc
require gcc-compile.inc
require gcc-install.inc
require gcc-package.inc

CT_NG = "make -rf `PATH=${PATH} which ct-ng`"
CT_NG[emit] = 'do_configure do_compile'
