# -*- mode:python; -*-

# Autoconf sitefile handling
inherit c
inherit siteinfo
inherit libtool
inherit make

EXTRA_OECONF[exclusive] = "configure"
EXTRA_OECONF:>machine		= " cross_compiling=yes"
EXTRA_OECONF:>cross		= " cross_compiling=yes"
EXTRA_OECONF:>sdk-cross		= " cross_compiling=yes"
EXTRA_OECONF:>sdk		= " cross_compiling=yes"
EXTRA_OECONF:>canadian-cross	= " cross_compiling=yes"

#EXTRA_OECONF += "--with-libtool=`which ${LIBTOOL}`"

# Arch tuple arguments for configure
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH} --host=${HOST_ARCH}"
OECONF_ARCHTUPLE:>cross			= " --target=${TARGET_ARCH}"
OECONF_ARCHTUPLE:>sdk-cross 		= " --target=${TARGET_ARCH}"
OECONF_ARCHTUPLE:>canadian-cross	= " --target=${TARGET_ARCH}"
OECONF_ARCHTUPLE[exclusive] = "configure"

autotools_configure () {
    if [ -x ${S}/configure ] ; then
        ${S}/configure \
 ${OECONF_ARCHTUPLE}\
 --prefix=${prefix} --exec_prefix=${exec_prefix}\
 --bindir=${bindir} --sbindir=${sbindir}\
 --libexecdir=${libexecdir} --datadir=${datadir} --sysconfdir=${sysconfdir}\
 --sharedstatedir=${sharedstatedir} --localstatedir=${localstatedir}\
 --libdir=${libdir} --includedir=${includedir}\
 --infodir=${infodir} --mandir=${mandir}\
 ${EXTRA_OECONF} $@
    else
        oefatal "no configure script found"
    fi
}
autotools_configure[exclusive] = "configure"

# OE compatibility/legacy function
# FIXME: remove at some point in time
oe_runconf () {
    autotools_configure
}
oe_runconf[exclusive] = "configure"

do_configure () {
    do_configure_autotools
}
do_configure_autotools[exclusive] = "configure"
do_configure_autotools () {
    if [ -f Makefile -a "${AUTOTOOLS_DISTCLEAN}" != "0" ] ; then
        ${MAKE} distclean || true
    fi

    if [ -e ${S}/configure ]; then
        oe_runconf
    else
        oenote "nothing to configure"
    fi

    libtool_script_fixup
}
AUTOTOOLS_DISTCLEAN ?= "1"
