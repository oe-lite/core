require ${PN}.inc

PR = "r1"

SRC_URI = "http://ymorin.is-a-geek.org/download/crosstool-ng/crosstool-ng-${PV}.tar.bz2"

# Official fixes
SRC_URI += "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/1.7.1/000-scripts_finish_do_not_try_to_symlink_if_sed_expr_is_a_no-op.patch;patch=1"
SRC_URI += "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/1.7.1/001-libc_uClibc_fix_snapshots.patch;patch=1"
SRC_URI += "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/1.7.1/002-configure_fix_--mandir.patch;patch=1"

# Canadian cross fixes by Martin Gaarde Lund
SRC_URI += "file://cloog-host-libstdcxx.patch;patch=1"
SRC_URI += "file://gcc-host-libstdcxx.patch;patch=1"
SRC_URI += "file://glibc-2.9-typedef-caddr.patch;patch=1"

S = "${WORKDIR}/${BPN}-${PV}"
