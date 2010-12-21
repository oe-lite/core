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

AUTOTOOLS_AUTORECONF ?= "0"
EXTRA_AUTORECONF = ""
acpaths = "__default__"

pkgltdldir = "${STAGE_DIR}/cross${stage_datadir}/libtool"
pkgltdldir_recipe-native    = "${STAGE_DIR}/native${stage_datadir}/libtool"
pkgltdldir_recipe-cross     = "${STAGE_DIR}/native${stage_datadir}/libtool"
pkgltdldir_recipe-sdk-cross = "${STAGE_DIR}/native${stage_datadir}/libtool"

autotools_autoreconf () {

    for ac in `find ${S} -name configure.in -o -name configure.ac`; do
        rm -f `dirname $ac`/configure
    done

    if [ -e ${S}/configure.in -o -e ${S}/configure.ac ]; then
        if [ "${acpaths}" = "__default__" ]; then
            acpaths=
            for i in `find ${S} -maxdepth 2 -name \*.m4|grep -v 'aclocal.m4'| \
                grep -v 'acinclude.m4' | sed -e 's,\(.*/\).*$,\1,'|sort -u`
            do
                acpaths="$acpaths -I $i"
            done
        else
            acpaths="${acpaths}"
        fi

        install -d ${TARGET_SYSROOT}${datadir}/aclocal
        acpaths="$acpaths -I${TARGET_SYSROOT}${datadir}/aclocal"
        install -d ${STAGE_DIR}/cross${stage_datadir}/aclocal
        acpaths="$acpaths -I${STAGE_DIR}/cross${stage_datadir}/aclocal"
        oenote acpaths=$acpaths

        # autoreconf is too shy to overwrite aclocal.m4 if it doesn't look
        # like it was auto-generated.  Work around this by blowing it away
        # by hand, unless the package specifically asked not to run aclocal.
        if ! echo ${EXTRA_AUTORECONF} | grep -q "aclocal"; then
            rm -f aclocal.m4
        fi

        if [ -e configure.in ]; then
            CONFIGURE_AC=configure.in
        else
            CONFIGURE_AC=configure.ac
        fi

        if grep "^[[:space:]]*AM_GLIB_GNU_GETTEXT" $CONFIGURE_AC >/dev/null; then
            if grep "sed.*POTFILES" $CONFIGURE_AC >/dev/null; then
                : do nothing -- we still have an old unmodified configure.ac
            else
                oenote Executing glib-gettextize --force --copy
                echo "no" | glib-gettextize --force --copy
            fi
        elif grep "^[[:space:]]*AM_GNU_GETTEXT" $CONFIGURE_AC >/dev/null; then
            if [ -e ${TARGET_SYSROOT}${datadir}/gettext/config.rpath ]; then
                cp ${TARGET_SYSROOT}${datadir}/gettext/config.rpath ${S}/
            else
                oenote config.rpath not found. gettext is not installed.
            fi
        fi

        mkdir -p m4

        export _lt_pkgdatadir="${pkgltdldir}"
        oenote Executing autoreconf
        autoreconf --verbose --install --force \
            ${EXTRA_AUTORECONF} $acpaths \
            || oefatal "autoreconf execution failed."
        if grep "^[[:space:]]*[AI][CT]_PROG_INTLTOOL" $CONFIGURE_AC >/dev/null; then
            oenote Executing intltoolize
            intltoolize --copy --force --automake
        fi
    fi
}

AUTOTOOLS_DISTCLEAN = "1"

autotools_do_configure () {
    if [ -f Makefile -a "${AUTOTOOLS_DISTCLEAN}" != "0" ] ; then
        ${MAKE} distclean || true
    fi

    if [ "${AUTOTOOLS_AUTORECONF}" != "0" ]; then
        autotools_autoreconf
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
