require conf/oe-lite-meta.conf
STAGE_FIXUP_FUNCS += "binconfig_fixup"
# INFO:

# solution 1.
# libdir:FIXEDSTRING ?


# solution 2.
# libdir -> =("?)libdir:=\1ROOT/libdir
# prefix/ -> =("?)prefix/:=\1ROOT/prefix/

# solution 3. (more exact, replace known paths )
# prefix=*
# exec_prefix=*
# includedir=*
# libdir=*
# datadir=*


# Then maby replace every /usr/ /var/ /opt/

# BINCONFIG_MANGLE += "libdir includedir datadir prefix exec_prefix "
# BINCONFIG_MANGLE_MISC += "-L${libdir} -I${includedir}"
# 


# # The namespaces can clash here hence the two step replace
# def get_binconfig_mangle(d):
# 	s = "-e ''"
# 	if not bb.data.inherits_class('native', d):
# 		optional_quote = r"\(\"\?\)"
# 		s += " -e 's:=%s${libdir}:=\\1OELIBDIR:;'" % optional_quote
# 		s += " -e 's:=%s${includedir}:=\\1OEINCDIR:;'" % optional_quote
# 		s += " -e 's:=%s${datadir}:=\\1OEDATADIR:'" % optional_quote
# 		s += " -e 's:=%s${prefix}/:=\\1OEPREFIX/:'" % optional_quote
# 		s += " -e 's:=%s${exec_prefix}/:=\\1OEEXECPREFIX/:'" % optional_quote
# 		s += " -e 's:-L${libdir}:-LOELIBDIR:;'"
# 		s += " -e 's:-I${includedir}:-IOEINCDIR:;'"

# 		s += " -e 's:OELIBDIR:${STAGING_LIBDIR}:;'"
# 		s += " -e 's:OEINCDIR:${STAGING_INCDIR}:;'"
# 		s += " -e 's:OEDATADIR:${STAGING_DATADIR}:'"
# 		s += " -e 's:OEPREFIX:${STAGING_DIR_HOST}${prefix}:'"
# 		s += " -e 's:OEEXECPREFIX:${STAGING_DIR_HOST}${exec_prefix}:'"



# 		s += " -e 's:OELIBDIR:${STAGING_LIBDIR}:;'"
# 		s += " -e 's:OEINCDIR:${STAGING_INCDIR}:;'"
# 		s += " -e 's:OEDATADIR:${STAGING_DATADIR}:'"
# 		s += " -e 's:OEPREFIX:${STAGING_DIR_HOST}${prefix}:'"
# 		s += " -e 's:OEEXECPREFIX:${STAGING_DIR_HOST}${exec_prefix}:'"

# 		s += " -e 's:-I${WORKDIR}:-I${STAGING_INCDIR}:'"
# 		s += " -e 's:-L${WORKDIR}:-L${STAGING_LIBDIR}:'"
# 		if bb.data.getVar("OE_BINCONFIG_EXTRA_MANGLE", d):
# 		    s += bb.data.getVar("OE_BINCONFIG_EXTRA_MANGLE", d)
# 	return s


#PACKAGE_PREPROCESS_FUNCS += "binconfig_package_preprocess"

# binconfig_package_preprocess () {
# 	for config in `find ${PKGD} -name '${BINCONFIG_GLOB}'`; do
# 		sed -i \
# 		    -e 's:${STAGING_LIBDIR}:${libdir}:g;' \ 
# 		    -e 's:${STAGING_INCDIR}:${includedir}:g;' \
# 		    -e 's:${STAGING_DATADIR}:${datadir}:' \
# 		    -e 's:${STAGING_DIR_HOST}${prefix}:${prefix}:' \
#                     $config
# 	done
# 	for lafile in `find ${PKGD} -name "*.la"` ; do
# 		sed -i \
# 		    -e 's:${STAGING_LIBDIR}:${libdir}:g;' \
# 		    -e 's:${STAGING_INCDIR}:${includedir}:g;' \
# 		    -e 's:${STAGING_DATADIR}:${datadir}:' \
# 		    -e 's:${STAGING_DIR_HOST}${prefix}:${prefix}:' \
# 		    $lafile
# 	done	    
# }

python binconfig_fixup () {
	import errno


	tempdir = bb.data.getVar('TEMP_STAGE_DIR', d, True)
	import glob
	os.chdir(tempdir)
        type_dir = ''.join(glob.glob('*'))
        os.chdir(type_dir)

	sd = bb.data.getVar('STAGE_DIR', d, True)+'/'+type_dir
	bb.note('sd '+sd)

	files = []
	try:
		f = open('.'+bb.data.getVar('binconfiglist', d, True), "r")
		files = f.readlines()
		f.close
	except IOError as exc:
		if exc.errno == errno.ENOENT:
			pass
		else: raise

	prefix = bb.data.getVar('prefix', d, True)
	exec_prefix = bb.data.getVar('exec_prefix', d, True)
	datadir = bb.data.getVar('datadir', d, True)
	bindir = bb.data.getVar('bindir', d, True)
	sbindir = bb.data.getVar('sbindir', d, True)
	libexecdir = bb.data.getVar('libexecdir', d, True)
	libdir = bb.data.getVar('libdir', d, True)
	includedir = bb.data.getVar('includedir', d, True)
	STAGE_DIR = bb.data.getVar('STAGE_DIR', d, True)

	import re, fileinput,sys
	for fn in files:
		for line in fileinput.FileInput(fn.rstrip(),inplace=1):
			line = re.sub(r'^(prefix=).*',r'\1'+sd+prefix,line)
			line = re.sub(r'^(exec_prefix=).*',r'\1'+sd+exec_prefix,line)
			line = re.sub(r'^(datadir=).*',r'\1'+sd+datadir,line)
			line = re.sub(r'^(bindir=).*',r'\1'+sd+bindir,line)
			line = re.sub(r'^(sbindir=).*',r'\1'+sd+sbindir,line)
			line = re.sub(r'^(libexecdir=).*',r'\1'+sd+libexecdir,line)
			line = re.sub(r'^(libdir=).*',r'\1'+sd+libdir,line)
			line = re.sub(r'^(includedir=).*',r'\1'+sd+includedir,line)
			# line = re.sub(r'-I'+includedir+'/',r'I'sd+includedir+'/',line)
			# line = re.sub(r'-L'+libdir+'/',r'-L'sd+libdir+'/',line)
			sys.stdout.write(line)
}
