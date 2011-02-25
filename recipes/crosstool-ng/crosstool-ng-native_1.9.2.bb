require ${PN}.inc

# Official fixes
FIXES_SRC_URI_BASE = "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/${PV}/"
SRC_URI += "${FIXES_SRC_URI_BASE}000-complibs_cloog_regenerate_autostuff_files.patch"
SRC_URI += "${FIXES_SRC_URI_BASE}001-libc_mingw_do_not_remove_support_symlink.patch"

# Unoffcial fixes
SRC_URI += "file://glibc-march-i686.patch"

# Add gcc 4.5.2 and glibc 2.11.2
SRC_URI += "file://gcc-4.5.2.patch"
SRC_URI += "file://glibc-2.11.2.patch"

# Fixup glibc-2.9 a bit
SRC_URI += "file://glibc-2.9-typedef-caddr.patch"
