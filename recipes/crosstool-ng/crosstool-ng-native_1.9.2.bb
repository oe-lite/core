require ${PN}.inc

# Official fixes
FIXES_SRC_URI_BASE = "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/${PV}/"
SRC_URI += "${FIXES_SRC_URI_BASE}000-complibs_cloog_regenerate_autostuff_files.patch"

# Unoffcial fixes
SRC_URI += "file://glibc-march-i686.patch"

# Add gcc 4.5.2 and glibc 2.11.2
SRC_URI += "file://gcc-4.5.2.patch"
SRC_URI += "file://glibc-2.11.2.patch"

# Add the TOOLCHAIN_VERSION's that is known to be working
PROVIDES_${PN} += "\
	crosstool-ng-native-gcc-4.3.4-glibc-2.9 \
	crosstool-ng-native-gcc-4.3.5-glibc-2.9 \
	crosstool-ng-native-gcc-4.3.5-glibc-2.10.1 \
	crosstool-ng-native-gcc-4.5.1-glibc-2.9 \
	crosstool-ng-native-gcc-4.5.1-glibc-2.10.1 \
	crosstool-ng-native-gcc-4.5.1-glibc-2.11 \
	crosstool-ng-native-gcc-4.5.1-glibc-2.11.1 \
	crosstool-ng-native-gcc-4.5.2-glibc-2.11.1 \
	crosstool-ng-native-gcc-4.5.2-glibc-2.11.2 \
	crosstool-ng-native-gcc-4.5.1-mingwrt-3.18 \
	crosstool-ng-native-gcc-4.5.2-mingwrt-3.18 \
"
