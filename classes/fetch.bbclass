addtask fetch
addtask fetchall after do_fetch
addtask unpack after do_fetch

FETCHER_DEPENDS = ""
DEPENDS_prepend += "${FETCHER_DEPENDS}"

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
