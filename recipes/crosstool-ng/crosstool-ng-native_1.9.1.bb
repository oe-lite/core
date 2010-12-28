require ${PN}.inc

SRC_URI = "http://ymorin.is-a-geek.org/download/crosstool-ng/crosstool-ng-${PV}.tar.bz2"

S = "${WORKDIR}/crosstool-ng-${PV}"

# Official fixes
FIXES_SRC_URI_BASE = "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/1.9.1/"
SRC_URI += "${FIXES_SRC_URI_BASE}000-config_fix_the_patch_fallbacks_methods.patch"
SRC_URI += "${FIXES_SRC_URI_BASE}001-libc_eglibc_fix_installed_scripts.patch"

# Add the TOOLCHAIN_VERSION's that is known to be working
PROVIDES_${PN} += "\
	crosstool-ng-native-gcc-4.5.1-glibc-2.9 \
	crosstool-ng-native-gcc-4.3.4-glibc-2.9 \
	crosstool-ng-native-gcc-4.5.1-mingwrt-3.18 \
"
