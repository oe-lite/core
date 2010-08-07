require ${PN}.inc

PR = "r1"

SRC_URI = "http://ymorin.is-a-geek.org/download/crosstool-ng/crosstool-ng-${PV}.tar.bz2"

S = "${WORKDIR}/crosstool-ng-${PV}"

# Official fixes
SRC_URI += "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/1.8.0/000-cc_gcc_with_static_ppl_correctly_link_with_libm.patch;patch=1"
SRC_URI += "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/1.8.0/001-complibs_cloog_with_static_ppl_correctly_link_with_libm.patch;patch=1"

# Canadian cross fixes by Martin Gaarde Lund
SRC_URI += "file://gcc-host-libstdcxx.patch;patch=1"
SRC_URI += "file://cloog-host-libstdcxx.patch;patch=1"
SRC_URI += "file://glibc-2.9-typedef-caddr.patch;patch=1"

# GCC 4.5.1 patch by Arnaud Lacombe
SRC_URI += "file://gcc-4.5.1.patch;patch=1"

# MinGW sysroot headers patch by Esben Haabendal
SRC_URI += "file://mingw-sysroot-headers-dir.patch;patch=1"

# Add the TOOLCHAIN_VERSION's that is known to be working
PROVIDES_${PN} += "\
	crosstool-ng-native-gcc-4.5.1-glibc-2.9 \
	crosstool-ng-native-gcc-4.3.4-glibc-2.9 \
	crosstool-ng-native-gcc-4.5.1-mingwrt-3.18 \
"
