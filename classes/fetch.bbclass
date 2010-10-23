addtask fetch after do_stage
addtask fetchall after do_fetch
addtask unpack after do_fetch

FETCHER_DEPENDS = ""
CLASS_DEPENDS += "${FETCHER_DEPENDS}"

do_fetch[dirs] = "${DL_DIR}"

python do_fetch() {
	import sys

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

	src_uri = bb.data.getVar('SRC_URI', localdata, 1)
	if not src_uri:
		return 1

	try:
		bb.fetch.init(src_uri.split(),d)
	except bb.fetch.NoMethodError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("No method: %s" % value)

	try:
		bb.fetch.go(localdata)
	except bb.fetch.MissingParameterError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("Missing parameters: %s" % value)
	except bb.fetch.FetchError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("Fetch failed: %s" % value)
	except bb.fetch.MD5SumError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("MD5  failed: %s" % value)
	except:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("Unknown fetch Error: %s" % value)

	return
}

do_fetchall[recrdeptask] = "do_fetch"

do_fetchall() {
	:
}

do_unpack[dirs] = "${WORKDIR}"

python do_unpack() {
	import re

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

	src_uri = bb.data.getVar('SRC_URI', localdata, True)
	if not src_uri:
		return

	for url in src_uri.split():
		try:
			local = bb.data.expand(bb.fetch.localpath(url, localdata), localdata)
		except bb.MalformedUrl, e:
			raise FuncFailed('Unable to generate local path for malformed uri: %s' % e)
		local = os.path.realpath(local)
		ret = oe_unpack_file(local, localdata, url)
		if not ret:
			raise bb.build.FuncFailed()
}


def oe_unpack_file(file, data, url = None):
	import subprocess
	if not url:
		url = "file://%s" % file
	dots = file.split(".")
	if dots[-1] in ['gz', 'bz2', 'Z']:
		efile = os.path.join(bb.data.getVar('WORKDIR', data, 1),os.path.basename('.'.join(dots[0:-1])))
	else:
		efile = file
	cmd = None
	if file.endswith('.tar'):
		cmd = 'tar x --no-same-owner -f %s' % file
	elif file.endswith('.tgz') or file.endswith('.tar.gz') or file.endswith('.tar.Z'):
		cmd = 'tar xz --no-same-owner -f %s' % file
	elif file.endswith('.tbz') or file.endswith('.tbz2') or file.endswith('.tar.bz2'):
		cmd = 'bzip2 -dc %s | tar x --no-same-owner -f -' % file
	elif file.endswith('.gz') or file.endswith('.Z') or file.endswith('.z'):
		cmd = 'gzip -dc %s > %s' % (file, efile)
	elif file.endswith('.bz2'):
		cmd = 'bzip2 -dc %s > %s' % (file, efile)
	elif file.endswith('.zip') or file.endswith('.jar'):
		cmd = 'unzip -q -o'
		(type, host, path, user, pswd, parm) = bb.decodeurl(url)
		if 'dos' in parm:
			cmd = '%s -a' % cmd
		cmd = "%s '%s'" % (cmd, file)
	elif os.path.isdir(file):
		filesdir = os.path.realpath(bb.data.getVar("FILESDIR", data, 1))
		destdir = "."
		if file[0:len(filesdir)] == filesdir:
			destdir = file[len(filesdir):file.rfind('/')]
			destdir = destdir.strip('/')
			if len(destdir) < 1:
				destdir = "."
			elif not os.access("%s/%s" % (os.getcwd(), destdir), os.F_OK):
				os.makedirs("%s/%s" % (os.getcwd(), destdir))
		cmd = 'cp -pPR %s %s/%s/' % (file, os.getcwd(), destdir)
	else:
		(type, host, path, user, pswd, parm) = bb.decodeurl(url)
		if not 'patch' in parm:
			# The "destdir" handling was specifically done for FILESPATH
			# items.  So, only do so for file:// entries.
			if type == "file":
				destdir = bb.decodeurl(url)[1] or "."
			else:
				destdir = "."
			bb.mkdirhier("%s/%s" % (os.getcwd(), destdir))
			cmd = 'cp %s %s/%s/' % (file, os.getcwd(), destdir)

	if not cmd:
		return True

	dest = os.path.join(os.getcwd(), os.path.basename(file))
	if os.path.exists(dest):
		if os.path.samefile(file, dest):
			return True

	# Change to subdir before executing command
	save_cwd = os.getcwd();
	parm = bb.decodeurl(url)[5]
	if 'subdir' in parm:
		newdir = ("%s/%s" % (os.getcwd(), parm['subdir']))
		bb.mkdirhier(newdir)
		os.chdir(newdir)

	cmd = "PATH=\"%s\" %s" % (bb.data.getVar('PATH', data, 1), cmd)
	bb.note("Unpacking %s to %s/" % (file, os.getcwd()))
	ret = subprocess.call(cmd, preexec_fn=subprocess_setup, shell=True)

	os.chdir(save_cwd)

	return ret == 0
