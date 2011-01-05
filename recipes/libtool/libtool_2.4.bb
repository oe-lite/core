require libtool-2.4.inc

SRC_URI += "\
    file://trailingslash.patch \
    file://prefix-manpage-fix.patch \
    file://resolve-sysroot.patch \
    file://use-sysroot-in-libpath.patch \
"
