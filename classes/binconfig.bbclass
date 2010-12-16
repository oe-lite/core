require conf/oe-lite-meta.conf
PACKAGES = "${PN}-dbg ${PN}-dev ${PN} ${PN}-doc ${PN}-locale"
BINCONFIG_GLOB += "${bindir}/*-config"
FILES_${PN}-dev += "${bindir}/*-config ${binconfigmetadir}"

FIXUP_FUNCS += "binconfig_metagen"

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

	prefix = bb.data.getVar('prefix', d, True)
	exec_prefix = bb.data.getVar('exec_prefix', d, True)
	datadir = bb.data.getVar('datadir', d, True)
	bindir = bb.data.getVar('bindir', d, True)
	sbindir = bb.data.getVar('sbindir', d, True)
	libexecdir = bb.data.getVar('libexecdir', d, True)
	libdir = bb.data.getVar('libdir', d, True)
	includedir = bb.data.getVar('includedir', d, True)
	binconfigmangle = bb.data.getVar('binconfigmangle', d, True)

	import ConfigParser
	fname = open('.'+binconfigmangle,"w")
	config = ConfigParser.ConfigParser()

	config.add_section("paths")
	config.set("paths","prefix",prefix)
	config.set("paths","exec_prefix",exec_prefix)
	config.set("paths","datadir",datadir)
	config.set("paths","bindir",bindir)
	config.set("paths","sbindir",sbindir)
	config.set("paths","libexecdir",libexecdir)
	config.set("paths","libdir",libdir)
	config.set("paths","includedir",includedir)
	config.write(fname)
	fname.close()
}
binconfig_metagen[dirs] = "${D}"
