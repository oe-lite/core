SECTION = "drivers"
DESCRIPTION = "Ethercat driver"
LICENSE = "GPLv2"

DEFAULT_PREFERENCE_mpc8313erdb = "1"
DEFAULT_PREFERENCE_awc500pcm = "1"

SRCREV_pn-ethercat = "131f655c03d3"
PR = "r7"

SRC_URI = "hg://etherlabmaster.hg.sourceforge.net:8000/hgroot/etherlabmaster;protocol=http;module=etherlabmaster \
	file://ethercat.conf \
	file://ip_link_control.patch;patch=1 \
"
S = "${WORKDIR}/etherlabmaster"

DEPENDS += "virtual/kernel"
PACKAGE_ARCH = "${MACHINE_ARCH}"

inherit autotools module

EXTRA_OECONF_mpc8313erdb = " \
	--with-linux-dir=${STAGING_DIR}/${MULTIMACH_HOST_SYS}/kernel \
	--enable-generic \
	--disable-8139too --disable-e100 --disable-e1000 --disable-r8169 \
	--enable-eoe \
	--disable-cycles \
	--enable-tool \
	--enable-userlib \
	--enable-tty \
	"
EXTRA_OECONF_awc500pcm = ${EXTRA_OECONF_mpc8313erdb}

MAKE_TARGETS = "modules"
do_compile () {
	oe_runmake all || die "make failed"

	sed -e 's%^MODINFO=.*%MODINFO=echo%' \
	    -e 's%^ETHERCAT_CONFIG=.*%ETHERCAT_CONFIG=${sysconfdir}/ethercat.conf%' \
	    < ${S}/script/init.d/ethercat > ${S}/script/init.d/ethercat.tmp
	mv ${S}/script/init.d/ethercat.tmp ${S}/script/init.d/ethercat

	module_do_compile
}

do_install () {
	oe_runmake DESTDIR="${D}" install

	unset CFLAGS CPPFLAGS CXXFLAGS LDFLAGS
	oe_runmake DESTDIR="${D}" INSTALL_MOD_PATH="${D}" CC="${KERNEL_CC}" LD="${KERNEL_LD}" modules_install

	rm -f ${D}/etc/sysconfig/ethercat
	rmdir ${D}/etc/sysconfig
	install -m 0644 ${WORKDIR}/ethercat.conf ${D}${sysconfdir}/
	ln -s ../init.d/ethercat ${D}${sysconfdir}/rcS.d/S05ethercat
}

PACKAGES += "${PN}-lib"

FILES_${PN} = "/etc /lib/modules ${bindir}"
FILES_${PN}-lib = "${libdir}/*.so.*"
FILES_${PN}-dev += "${libdir}/*.so ${libdir}/*.so ${prefix}/modules/*.symvers"

RDEPENDS_${PN}-dev = "${PN}-lib"
