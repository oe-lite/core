DEFAULT_PREFERENCE = "-1"

require libtool-common.inc

EXTRA_OECONF += "--with-sysroot=${TARGET_SYSROOT}"
