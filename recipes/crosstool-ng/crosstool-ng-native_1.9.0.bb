require ${PN}.inc

SRC_URI = "http://ymorin.is-a-geek.org/download/crosstool-ng/crosstool-ng-${PV}.tar.bz2"

S = "${WORKDIR}/crosstool-ng-${PV}"

# Official fixes
FIXES_SRC_URI_BASE = "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/1.9.0/"
SRC_URI += "${FIXES_SRC_URI_BASE}000-libc_eglibc_fix_downloading.patch"
SRC_URI += "${FIXES_SRC_URI_BASE}001-scripts_xldd_install_only_when_shared_libs_enabled.patch"
SRC_URI += "${FIXES_SRC_URI_BASE}002-scripts_xldd_fix_typoes.patch"
SRC_URI += "${FIXES_SRC_URI_BASE}003-scripts_xldd_fix_version_string.patch"
SRC_URI += "${FIXES_SRC_URI_BASE}004-scripts_xldd_stop_at_first_match.patch"
SRC_URI += "${FIXES_SRC_URI_BASE}005-scripts_xldd_better_find_sysroot_with_old_gcc.patch"

# Canadian cross fixes by Martin Gaarde Lund
#SRC_URI += "file://gcc-host-libstdcxx.patch;patch=1"
#SRC_URI += "file://cloog-host-libstdcxx.patch;patch=1"
#SRC_URI += "file://glibc-2.9-typedef-caddr.patch;patch=1"

# Add the TOOLCHAIN_VERSION's that is known to be working
PROVIDES_${PN} += "\
	crosstool-ng-native-gcc-4.5.1-glibc-2.9 \
	crosstool-ng-native-gcc-4.3.4-glibc-2.9 \
	crosstool-ng-native-gcc-4.5.1-mingwrt-3.18 \
"
