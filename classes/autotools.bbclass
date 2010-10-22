# Autoconf sitefile handling
inherit siteinfo

EXTRA_OEMAKE = ""

AUTOTOOLS_LIBTOOL_DEPENDS = "${HOST_ARCH}/libtool"
AUTOTOOLS_LIBTOOL_DEPENDS_recipe-native = "libtool-native"
AUTOTOOLS_DEPENDS = "autoconf-native automake-native ${AUTOTOOLS_LIBTOOL_DEPENDS}"
DEPENDS_prepend += "${AUTOTOOLS_DEPENDS}"

acpaths = "default"
EXTRA_AUTORECONF = "--exclude=autopoint"

EXTRA_OECONF_append += "${@autotools_crosscompiling(d)}"
def autotools_crosscompiling(d):
	if not bb.data.inherits_class('native', d):
		return "cross_compiling=yes"
	return ""

# Libtool commands
BUILD_LIBTOOL	= "${BUILD_PREFIX}libtool"
HOST_LIBTOOL	= "${HOST_PREFIX}libtool"
TARGET_LIBTOOL	= "${TARGET_PREFIX}libtool"
LIBTOOL	= "${HOST_LIBTOOL}"
export LIBTOOL
#EXTRA_OECONF_append += "--with-libtool=`which ${LIBTOOL}`"

# Arch tuple arguments for configure
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH} --host=${HOST_ARCH}"

oe_runconf () {
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

AUTOTOOLS_AUTORECONF ?= "0"
EXTRA_AUTORECONF = ""
acpaths = "__default__"

autotools_autoreconf() {

	for ac in `find ${S} -name configure.in -o -name configure.ac`; do
       		rm -f `dirname $ac`/configure
	done

	if [ -e ${S}/configure.in -o -e ${S}/configure.ac ]; then
		if [ "${acpaths}" = "__default__" ]; then
			acpaths=
			for i in `find ${S} -maxdepth 2 -name \*.m4|grep -v 'aclocal.m4'| \
				grep -v 'acinclude.m4' | sed -e 's,\(.*/\).*$,\1,'|sort -u`; do
				acpaths="$acpaths -I $i"
			done
		else
			acpaths="${acpaths}"
		fi

		#AUTOV=`automake --version |head -n 1 |sed "s/.* //;s/\.[0-9]\+$//"`
		#automake --version
		#echo "AUTOV is $AUTOV"
		#install -d ${STAGING_DATADIR}/aclocal
		#install -d ${STAGING_DATADIR}/aclocal-$AUTOV
		#acpaths="$acpaths -I${STAGING_DATADIR}/aclocal-$AUTOV -I ${STAGING_DATADIR}/aclocal"

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

		#if grep "^[[:space:]]*AM_GLIB_GNU_GETTEXT" $CONFIGURE_AC >/dev/null; then
		#  if grep "sed.*POTFILES" $CONFIGURE_AC >/dev/null; then
		#    : do nothing -- we still have an old unmodified configure.ac
		#  else
		#    oenote Executing glib-gettextize --force --copy
		#    echo "no" | glib-gettextize --force --copy
		#  fi
		#else if grep "^[[:space:]]*AM_GNU_GETTEXT" $CONFIGURE_AC >/dev/null; then
		#  if [ -e ${STAGING_DATADIR}/gettext/config.rpath ]; then
		#    cp ${STAGING_DATADIR}/gettext/config.rpath ${S}/
		#  else
		#    oenote ${STAGING_DATADIR}/gettext/config.rpath not found. gettext is not installed.
		#  fi
		#fi
		
		#fi

		mkdir -p m4

		oenote Executing autoreconf --verbose --install --force ${EXTRA_AUTORECONF} $acpaths
		autoreconf -Wcross --verbose --install --force ${EXTRA_AUTORECONF} $acpaths || oefatal "autoreconf execution failed."
		if grep "^[[:space:]]*[AI][CT]_PROG_INTLTOOL" $CONFIGURE_AC >/dev/null; then
		  oenote Executing intltoolize --copy --force --automake
		  intltoolize --copy --force --automake
		fi
	fi

}

AUTOTOOLS_LIBTOOL_FIXUP				= "libtool"
AUTOTOOLS_LIBTOOL_FIXUP_recipe-native		= ""
AUTOTOOLS_LIBTOOL_FIXUP_recipe-cross		= ""
AUTOTOOLS_LIBTOOL_FIXUP_recipe-sdk-cross	= ""

autotools_libtool_fixup () {
	oenote autotools_libtool_fixup
	pwd
	for file in ${AUTOTOOLS_LIBTOOL_FIXUP} ; do
		if [ -f $file ]; then
			rm -f $file
			ln -s ${STAGE_DIR}/cross${stage_bindir}/${HOST_PREFIX}libtool $file
		fi
	done
}

autotools_do_configure() {

	if [ "${AUTOTOOLS_AUTORECONF}" != "0" ]; then
		autotools_autoreconf
	fi

	if [ -e ${S}/configure ]; then
		oe_runconf
	else
		oenote "nothing to configure"
	fi

	if [ -n "${AUTOTOOLS_LIBTOOL_FIXUP}" ]; then
		autotools_libtool_fixup
	fi
}

autotools_do_install() {
	oe_runmake 'DESTDIR=${D}' install
}

PACKAGE_PREPROCESS_FUNCS += "autotools_prepackage_lamangler"

autotools_prepackage_lamangler () {
        for i in `find ${PKGD} -name "*.la"` ; do \
            sed -i -e 's:${STAGING_LIBDIR}:${libdir}:g;' \
                   -e 's:${D}::g;' \
                   -e 's:-I${WORKDIR}\S*: :g;' \
                   -e 's:-L${WORKDIR}\S*: :g;' \
                   $i
	done
}

EXPORT_FUNCTIONS do_configure do_install
