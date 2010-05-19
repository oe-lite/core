EXTRA_OEMAKE = ""

AUTOTOOLS_DEPENDS = "autoconf-native automake-native ${HOST_ARCH}-libtool"
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
export LIBTOOL	= "${HOST_LIBTOOL}"
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

autotools_do_configure() {
	if [ -e ${S}/configure ]; then
		oe_runconf
	else
		oenote "nothing to configure"
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

# STAGE_TEMP_PREFIX is used for a speedup by packaged-staging
STAGE_TEMP="${WORKDIR}/temp-staging"
STAGE_TEMP_PREFIX = ""

autotools_stage_includes() {
	if [ "${INHIBIT_AUTO_STAGE_INCLUDES}" != "1" ]
	then
		rm -rf ${STAGE_TEMP}
		mkdir -p ${STAGE_TEMP}
		make DESTDIR="${STAGE_TEMP}" install
		cp -pPR ${STAGE_TEMP}/${includedir}/* ${STAGING_INCDIR}
		rm -rf ${STAGE_TEMP}
	fi
}

autotools_stage_dir() {
 	sysroot_stage_dir $1 ${STAGE_TEMP_PREFIX}$2
}

autotools_stage_libdir() {
	sysroot_stage_libdir $1 ${STAGE_TEMP_PREFIX}$2
}

autotools_stage_all() {
	if [ "${INHIBIT_AUTO_STAGE}" = "1" ]
	then
		return
	fi
	rm -rf ${STAGE_TEMP}
	mkdir -p ${STAGE_TEMP}
	oe_runmake DESTDIR="${STAGE_TEMP}" install
	rm -rf ${STAGE_TEMP}/${mandir} || true
	rm -rf ${STAGE_TEMP}/${infodir} || true
	sysroot_stage_dirs ${STAGE_TEMP} ${STAGE_TEMP_PREFIX}
	rm -rf ${STAGE_TEMP}
}

EXPORT_FUNCTIONS do_configure do_install

