# Autoconf sitefile handling
inherit siteinfo

inherit libtool

EXTRA_OEMAKE = ""

autotools_crosscompiling = "cross_compiling=yes"
autotools_crosscompiling_recipe-native = ""
EXTRA_OECONF += "${autotools_crosscompiling}"

#EXTRA_OECONF += "--with-libtool=`which ${LIBTOOL}`"

# Arch tuple arguments for configure
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH} --host=${HOST_ARCH}"

autotools_configure () {
    if [ -x ${S}/configure ] ; then
        cfgcmd="${S}/configure \
            ${OECONF_ARCHTUPLE} \
            --prefix=${prefix} \
            --exec_prefix=${exec_prefix} \
            --bindir=${bindir} \
            --sbindir=${sbindir} \
            --libexecdir=${libexecdir} \
            --datadir=${datadir} \
            --sysconfdir=${sysconfdir} \
            --sharedstatedir=${sharedstatedir} \
            --localstatedir=${localstatedir} \
            --libdir=${libdir} \
            --includedir=${includedir} \
            --infodir=${infodir} \
            --mandir=${mandir} \
            ${EXTRA_OECONF} \
            $@"
        oenote "Running $cfgcmd..."
        $cfgcmd || oefatal "oe_runconf failed"
    else
        oefatal "no configure script found"
    fi
}

# OE compatibility/legacy function
oe_runconf () {
    autotools_configure
}

AUTOTOOLS_DISTCLEAN = "1"

autotools_do_configure () {
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

do_configure () {
    autotools_do_configure
}

autotools_do_install () {
    oe_runmake 'DESTDIR=${D}' install
}

do_install () {
    autotools_do_install
}
