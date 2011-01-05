addtask fetch after do_stage_fixup
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
        bb.fetch.init(src_uri.split(), localdata)
    except bb.fetch.NoMethodError:
        (type, value, traceback) = sys.exc_info()
        raise bb.build.FuncFailed("No method: %s" % value)
    except bb.MalformedUrl:
        (type, value, traceback) = sys.exc_info()
        raise bb.build.FuncFailed("Malformed URL: %s" % value)

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

do_fetchall[recadeptask] = "do_fetch"
do_fetchall[nostamp] = True
do_fetchall[func] = True
do_fetchall = ""

do_unpack[dirs] = "${SRCDIR}"
do_unpack[cleandirs] = "${SRCDIR}"

python do_unpack() {
    from glob import glob

    localdata = bb.data.createCopy(d)
    bb.data.update_data(localdata)

    dl_dir = localdata.getVar("DL_DIR", True)
    src_uri = localdata.getVar("SRC_URI", True)
    if not src_uri:
        return
    srcurldata = bb.fetch.init(src_uri.split(), localdata)
    filespath = localdata.getVar("FILESPATH", True).split(":")

    def oe_unpack(d, local, urldata):
        from oe.unpack import unpack_file, is_patch, UnpackError
        if is_patch(local, urldata.parm):
            return

        subdirs = []
        if "subdir" in urldata.parm:
            subdirs.append(urldata.parm["subdir"])

        if urldata.type == "file":
            if not urldata.host:
                urlpath = urldata.path
            else:
                urlpath = "%s%s" % (urldata.host, urldata.path)

            if not os.path.isabs(urlpath):
                subdirs.append(os.path.dirname(urlpath))

        srcdir = d.getVar("SRCDIR", True)

        if subdirs:
            destdir = oe.path.join(srcdir, *subdirs)
            bb.mkdirhier(destdir)
        else:
            destdir = srcdir
        dos = urldata.parm.get("dos")

        bb.note("Unpacking %s to %s/" % (base_path_out(local, d),
                                         base_path_out(destdir, d)))
        try:
            unpack_file(local, destdir, env={"PATH": d.getVar("PATH", True)},
                        dos=dos)
        except UnpackError, exc:
            bb.fatal(str(exc))


    for url in src_uri.split():
        urldata = srcurldata[url]
        if urldata.type == "file" and "*" in urldata.path:
            # The fetch code doesn't know how to handle globs, so
            # we need to handle the local bits ourselves
            for path in filespath:
                srcdir = oe.path.join(path, urldata.host,
                                      os.path.dirname(urldata.path))
                if os.path.exists(srcdir):
                    break
            else:
                bb.fatal("Unable to locate files for %s" % url)

            for filename in glob(oe.path.join(srcdir,
                                              os.path.basename(urldata.path))):
                oe_unpack(localdata, filename, urldata)
        else:
            local = urldata.localpath
            if not local:
                raise bb.build.FuncFailed('Unable to locate local file for %s' % url)

            # FIXME: I don't think it _should_ be needed, but we have
            # to prepend DL_DIR in some cases (ie. calling do_unpack
            # after do_fetch).
            #local = os.path.join(dl_dir, local)

            oe_unpack(localdata, local, urldata)
}
