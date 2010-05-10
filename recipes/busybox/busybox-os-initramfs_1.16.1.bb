require busybox_${PV}.bb
INC_PR = ".1"

S="${WORKDIR}/busybox-${PV}"

FILESPATH=${@base_set_filespath([ "${FILE_DIRNAME}/${PF}", "${FILE_DIRNAME}/${P}", "${FILE_DIRNAME}/${PN}", "${FILE_DIRNAME}/${BP}", "${FILE_DIRNAME}/${BPN}", "${FILE_DIRNAME}/busybox-${PV}-${PR}", "${FILE_DIRNAME}/busybox-${PV}", "${FILE_DIRNAME}/busybox", "${FILE_DIRNAME}/files", "${FILE_DIRNAME}" ], d)}

RDEPENDS_${PN} = "netbase base-passwd base-files ${TARGET_CROSS}-toolchain-sysroot"
