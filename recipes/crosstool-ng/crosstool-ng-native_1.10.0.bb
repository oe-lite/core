require ${PN}.inc

# Official fixes
FIXES_SRC_URI_BASE = "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/${PV}/"

# Unoffcial fixes
SRC_URI += "file://glibc-march-i686.patch"
SRC_URI += "file://glibc-typedef-caddr.patch"