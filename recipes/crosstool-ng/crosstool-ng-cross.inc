INC_PR = ".0"

inherit cross

require crosstool-ng.inc

PROVIDES = "gcc-cross-${TARGET_ARCH}"

staging_dir = "${WORKDIR}/staging"

do_stage () {
	rm -rf ${staging_dir}
	cp -dpR ${B} ${staging_dir}

	rm -f ${staging_dir}/build.log
	rm -f ${staging_dir}/lib/libiberty.a
	rm -f ${staging_dir}/bin/${TARGET_ARCH}-gcc-?.?.*
	rm -rf ${staging_dir}/${TARGET_ARCH}/sys-root${layout_datadir}/locale

	mkdir -p ${STAGING_DIR}/target
	cp -dpR ${staging_dir}/* ${STAGING_DIR}/target
}

#PACKAGES = "\
#  libmudflap libmudflap-dev \
#  libgcc-dev \
#"
#
#FILES_libgcc		= "${layout_base_libdir}/libgcc*.so.*"
#FILES_libgcc-dev	= "${layout_base_libdir}/libgcc*.so"
#
#
#FILES_libmudflap	= "${layout_base_libdir}/libmudflap*.so.*"
#FILES_libmudflap-dev	= "\
#			   ${layout_base_libdir}/libmudflap*.so \
#			   ${layout_base_libdir}/libmudflap*.a \
#			   ${layout_base_libdir}/libmudflap*.la \
#			  "
#
#sysroot_dir = "${B}/${TARGET_ARCH}/sys-root"
#
#do_install () {
#
#	mkdir -p ${D}${layout_base_libdir}
#	if [ -f ${sysroot_dir}${layout_base_libdir}/nof/libgcc_s.so ]; then
#		cp -dp ${sysroot_dir}${layout_base_libdir}/nof/libgcc_s.so.* ${D}${layout_base_libdir}
#	else
#		cp -dp ${sysroot_dir}${layout_base_libdir}/libgcc_s.so.* ${D}${layout_base_libdir} || true
#	fi
#
#	mkdir -p ${D}${layout_sysconfdir}
#	cp -dpR ${sysroot_dir}${layout_sysconfdir}/* ${D}${layout_sysconfdir}/
#
#	mkdir -p ${D}${layout_base_sbindir}
#	cp -dpR ${sysroot_dir}${layout_base_sbindir}/* ${D}${layout_base_sbindir}
#
#	mkdir -p ${D}${layout_bindir}
#	cp -dpR ${sysroot_dir}${layout_bindir}/* ${D}${layout_bindir}
#
#	mkdir -p ${D}${layout_base_libdir}
#	cp -dp ${sysroot_dir}${layout_base_libdir}/*.so.* \
#		${sysroot_dir}${layout_base_libdir}/*.so \
#		${D}${layout_base_libdir}
#
#	mkdir -p ${D}${layout_libdir}
#	cp -dp ${sysroot_dir}${layout_libdir}/*.so \
#		${D}${layout_libdir}
#}
