DESCRIPTION = "BusyBox combines tiny versions of many common UNIX utilities into a single \
small executable. It provides minimalist replacements for most of the \
utilities you usually find in GNU fileutils, shellutils, etc. The utilities \
in BusyBox generally have fewer options than their full-featured GNU \
cousins; however, the options that are included provide the expected \
functionality and behave very much like their GNU counterparts. BusyBox \
provides a fairly complete POSIX environment for any small or embedded \
system."
HOMEPAGE = "http://www.busybox.net"
LICENSE = "GPL"
SECTION = "base"
PRIORITY = "required"

PR = "r21${INC_PR}"

SRC_URI_append = "\
	file://busybox-cron \
	file://busybox-httpd \
	file://busybox-udhcpd \
	file://busybox-mdev \
	file://syslogd.sh \
	file://inetd.sh \
	file://inetd.conf \
	file://mdev.conf \
	file://default.script \
	file://hwclock.sh \
	file://mount.busybox \
	file://umount.busybox \
	file://defconfig \
	file://inittab \
	file://rcS \
	file://rc \
	file://rcS-default \
	file://resolv.conf \
	file://ntpd.sh \
	file://shutdown.sh \
	"

PACKAGES =+ "${PN}-inetd ${PN}-syslogd ${PN}-crond ${PN}-httpd ${PN}-udhcpd ${PN}-hwclock ${PN}-mdev ${PN}-ntpd ${PN}-shutdown"

DEPENDS_${PN} = "${TARGET_CROSS}-toolchain"
RDEPENDS_${PN} = "${TARGET_CROSS}-toolchain-sysroot"

FILES_${PN}-inetd = "${sysconfdir}/init.d/inetd.sh ${sysconfdir}/inetd.conf"
FILES_${PN}-crond = "${sysconfdir}/init.d/busybox-crond"
FILES_${PN}-syslogd = "${sysconfdir}/init.d/syslogd.sh"
FILES_${PN}-httpd = "${sysconfdir}/init.d/busybox-httpd /srv/www"
FILES_${PN}-udhcpd = "${sysconfdir}/init.d/busybox-udhcpd"
FILES_${PN}-hwclock = "${sysconfdir}/init.d/hwclock"
FILES_${PN}-mdev = "${sysconfdir}/init.d/busybox-mdev ${sysconfdir}/mdev.conf"
FILES_${PN}-ntpd = "${sysconfdir}/init.d/ntpd.sh"
FILES_${PN}-shutdown = "${sysconfdir}/init.d/shutdown.sh"

FILES_${PN} += "${datadir}/udhcpc"

INITSCRIPT_PACKAGES = "${PN} ${PN}-crond ${PN}-httpd ${PN}-udhcpd ${PN}-hwclock ${PN}-mdev ${PN}-syslogd ${PN}-inetd ${PN}-ntpd ${PN}-shutdown"
INITSCRIPT_NAME_${PN}-crond = "busybox-crond"
INITSCRIPT_NAME_${PN}-httpd = "busybox-httpd"
INITSCRIPT_NAME_${PN}-udhcpd = "busybox-udhcpd" 
INITSCRIPT_NAME_${PN}-hwclock = "hwclock"
INITSCRIPT_PARAMS_${PN}-hwclock = "start 15 S . stop 20 0 ."
INITSCRIPT_NAME_${PN}-mdev = "busybox-mdev"
INITSCRIPT_PARAMS_${PN}-mdev = "start 10 S ."
INITSCRIPT_NAME_${PN}-syslogd = "syslogd.sh"
INITSCRIPT_PARAMS_${PN}-syslogd = "start 21 S ."
INITSCRIPT_NAME_${PN}-inetd = "inetd.sh"
INITSCRIPT_PARAMS_${PN}-inetd = "start 26 S ."
CONFFILES_${PN}-mdev = "${sysconfdir}/mdev.conf"
CONFFILES_${PN}-inetd = "${sysconfdir}/inetd.conf"
INITSCRIPT_NAME_${PN}-ntpd = "ntpd.sh"
INITSCRIPT_PARAMS_${PN}-ntpd = "start 70 S ."
INITSCRIPT_NAME_${PN}-shutdown = "shutdown.sh"
INITSCRIPT_PARAMS_${PN}-shutdown = "stop 98 0 ."

inherit cml1 update-rc.d

export EXTRA_CFLAGS = "${CFLAGS}"
EXTRA_OEMAKE += "V=1 ARCH=${TARGET_ARCH} CROSS_COMPILE=${TARGET_PREFIX}"
EXTRA_OEMAKE += "CROSS=${HOST_PREFIX}"

do_configure_prepend () {
	install -m 0644 ${WORKDIR}/defconfig ${S}/.config
}

do_compile() {
	unset CFLAGS CPPFLAGS CXXFLAGS LDFLAGS
	base_do_compile
}

do_install () {
	unset CFLAGS CPPFLAGS CXXFLAGS LDFLAGS
	install -d ${D}${sysconfdir}/init.d
	oe_runmake "PREFIX=${D}" install
	cp -pPR ${S}/_install/* ${D}/

	# Move everything to /busybox (not supposed to end up in any package)
	install -d ${D}/busybox
	ls ${D} -R

	cp -dPr ${D}${base_bindir} ${D}${base_sbindir} ${D}${prefix} ${D}/busybox/
	# Move the busybox binary back to /bin
	install -d ${D}${base_bindir}
	mv ${D}/busybox${base_bindir}/busybox ${D}${base_bindir}/
	# Move back the sh symlink
	test -h ${D}/busybox${base_bindir}/sh && mv ${D}/busybox${base_bindir}/sh ${D}${base_bindir}/

	if grep "CONFIG_CROND=y" ${WORKDIR}/defconfig; then
		# Move crond back to /usr/sbin/crond
		install -d ${D}${sbindir}
		mv ${D}/busybox${sbindir}/crond ${D}${sbindir}/

		install -m 0755 ${WORKDIR}/busybox-cron ${D}${sysconfdir}/init.d/
	fi
	if grep "CONFIG_HTTPD=y" ${WORKDIR}/defconfig; then
		# Move httpd back to /usr/sbin/httpd
		install -d ${D}${sbindir}
		mv ${D}/busybox${sbindir}/httpd ${D}${sbindir}/

		install -m 0755 ${WORKDIR}/busybox-httpd ${D}${sysconfdir}/init.d/
		install -d ${D}/srv/www
	fi
	if grep "CONFIG_APP_UDHCPD=y" ${WORKDIR}/defconfig; then
		# Move udhcpd back to /usr/sbin/udhcpd
		install -d ${D}${sbindir}
		mv ${D}/busybox${sbindir}/udhcpd ${D}${sbindir}/

		install -m 0755 ${WORKDIR}/busybox-udhcpd ${D}${sysconfdir}/init.d/
	fi
	if grep "CONFIG_HWCLOCK=y" ${WORKDIR}/defconfig; then
		# Move hwclock back to /sbin/hwclock
		install -d ${D}${base_sbindir}
		mv ${D}/busybox${base_sbindir}/hwclock ${D}${base_sbindir}/

		install -m 0755 ${WORKDIR}/hwclock.sh ${D}${sysconfdir}/init.d/hwclock
	fi
	if grep "CONFIG_MDEV=y" ${WORKDIR}/defconfig; then
		# Move mdev back to /sbin/udhcpd
		install -d ${D}${base_sbindir}
		mv ${D}/busybox${base_sbindir}/mdev ${D}${base_sbindir}/

		install -m 0644 ${WORKDIR}/mdev.conf ${D}${sysconfdir}/
		install -m 0755 ${WORKDIR}/busybox-mdev ${D}${sysconfdir}/init.d/
	fi
	if grep "CONFIG_INETD=y" ${WORKDIR}/defconfig; then
		install -m 0644 ${WORKDIR}/inetd.conf ${D}${sysconfdir}/
		install -m 0755 ${WORKDIR}/inetd.sh ${D}${sysconfdir}/init.d/
	fi
	if grep "CONFIG_UDHCPC=y" ${WORKDIR}/defconfig; then
		# Move dhcpc back to /usr/sbin/udhcpc
		install -d ${D}${base_sbindir}
		mv ${D}/busybox${base_sbindir}/udhcpc ${D}${base_sbindir}/

		install -d ${D}${sysconfdir}/udhcpc.d
		install -d ${D}${datadir}/udhcpc
		install -m 0755 ${S}/examples/udhcp/simple.script ${D}${sysconfdir}/udhcpc.d/50default
		install -m 0755 ${WORKDIR}/default.script ${D}${datadir}/udhcpc/default.script
	fi
	if grep "CONFIG_MODPROBE_SMALL=y" ${WORKDIR}/defconfig; then
		install -d ${D}${sysconfdir}/modules
	fi
	if grep "CONFIG_SYSLOGD=y" ${WORKDIR}/defconfig; then
		install -d ${D}${localstatedir}/log
		install -m 0755 ${WORKDIR}/syslogd.sh ${D}${sysconfdir}/init.d/
	fi
	if grep "CONFIG_NTPD=y" ${WORKDIR}/defconfig; then
		install -m 0755 ${WORKDIR}/ntpd.sh ${D}${sysconfdir}/init.d/
	fi

	install -m 0755 ${WORKDIR}/shutdown.sh ${D}${sysconfdir}/init.d/
	install -m 0644 ${S}/busybox.links ${D}${sysconfdir}

	install -m 644 ${WORKDIR}/inittab ${D}${sysconfdir}/
	install -m 755 ${WORKDIR}/rcS ${D}${sysconfdir}/init.d/rcS
	install -m 755 ${WORKDIR}/rc ${D}${sysconfdir}/init.d/rc
	install -d ${D}${sysconfdir}/default
	install -m 755 ${WORKDIR}/rcS-default ${D}${sysconfdir}/default/rcS
	install -m 644 ${WORKDIR}/resolv.conf ${D}${sysconfdir}/
}

pkg_postinst_${PN} () {
	# If we are not making an image we create links for the utilities that doesn't exist
	# so the update-alternatives script will get the utilities it needs
	# (update-alternatives have no problem replacing links later anyway)
	test -n 2> /dev/null || alias test='busybox test'
	if test "x$D" = "x"; then while read link; do if test ! -h "$link"; then case "$link" in /*/*/*) to="../../bin/busybox";; /bin/*) to="busybox";; /*/*) to="../bin/busybox";; esac; busybox ln -s $to $link; fi; done </etc/busybox.links; fi
	
	# This adds the links, remember that this has to work when building an image too, hence the $D
	while read link; do case "$link" in /*/*/*) to="../../bin/busybox";; /bin/*) to="busybox";; /*/*) to="../bin/busybox";; esac; bn=`basename $link`; update-alternatives --install $link $bn $to 50; done <$D/etc/busybox.links
}

pkg_prerm_${PN} () {
	# This is so you can make busybox commit suicide - removing busybox with no other packages
	# providing its files, this will make update-alternatives work, but the update-rc.d part
	# for syslog, httpd and/or udhcpd will fail if there is no other package providing sh
	tmpdir=`mktemp -d /tmp/busyboxrm-XXXXXX`
	ln -s /bin/busybox $tmpdir/[
	ln -s /bin/busybox $tmpdir/test
	ln -s /bin/busybox $tmpdir/head
	ln -s /bin/busybox $tmpdir/sh
	ln -s /bin/busybox $tmpdir/basename
	ln -s /bin/busybox $tmpdir/echo
	ln -s /bin/busybox $tmpdir/mv
	ln -s /bin/busybox $tmpdir/ln
	ln -s /bin/busybox $tmpdir/dirname
	ln -s /bin/busybox $tmpdir/rm
	ln -s /bin/busybox $tmpdir/sed
	ln -s /bin/busybox $tmpdir/sort
	export PATH=$PATH:$tmpdir

	while read link
	do
		case "$link" in
			/*/*/*) to="../../bin/busybox";;
			/bin/*) to="busybox";;
			/*/*) to="../bin/busybox";;
		esac
		bn=`basename $link`
		sh /usr/bin/update-alternatives --remove $bn $to
	done </etc/busybox.links
}
