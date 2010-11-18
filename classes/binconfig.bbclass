require conf/oe-lite-meta.conf
BINCONFIG_GLOB += "${bindir}/*-config"
FILES_${PN}-dev += "${BINCONFIG_GLOB} ${binconfigmetadir}"

INSTALL_FIXUP_FUNCS += "binconfig_metagen"


python binconfig_metagen () {
	def mkdir_p(path):
		import errno
		try:
			os.makedirs(path)
		except OSError as exc:
			if exc.errno == errno.EEXIST:
				pass
			else: raise
	
	metadir = bb.data.getVar('binconfigmetadir', d, True)
	meta_file = bb.data.getVar('binconfiglist', d, True)
	mkdir_p('.'+metadir)

	import glob
	config_list = []
	for pattern in bb.data.getVar('BINCONFIG_GLOB', d, True).split():
		bb.note(pattern)
		config_list += glob.glob('.'+pattern)

	f = open('.'+meta_file, "w")
	f.write("\n".join(str(x) for x in config_list) + '\n')
	f.close()
}
binconfig_metagen[dirs] = "${D}"
