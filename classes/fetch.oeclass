# -*- mode:python; -*-

addtask fetch after stage_fixup
addtask unpack after fetch
addtask patch after unpack

FETCHER_DEPENDS = ""
CLASS_DEPENDS += "${FETCHER_DEPENDS}"


addhook fetch_init to post_recipe_parse first after set_useflags

addhook fetch_init_signatures to mid_recipe_parse

def fetch_init_signatures(d):
    import oelite.fetch
    sigfilename = d.get("SIGNATURE_FILE")
    d.set_input_mtime(sigfilename)
    d["__fetch_signatures"] = oelite.fetch.SignatureFile(sigfilename)

def fetch_init(d):
    import oelite.fetch
    import hashlib
    m = hashlib.sha1()
    uris = []
    schemes = set()
    failed = False
    filespath = d.get("FILESPATH").split(":")
    d["FILESPATH_EXISTS"] = ":".join([
            p for p in filespath if os.path.exists(p)])
    for src_uri in (d.get("SRC_URI") or "").split():
        try:
            uri = oelite.fetch.OEliteUri(src_uri, d)
            m.update(uri.signature())
            schemes.add(uri.scheme)
            uris.append(uri)
        except oelite.fetch.FetchException as e:
            print e
            failed = True
    if failed:
        print "Bad SRC_URI"
        return False
    d.set("SRC_URI_SIGNATURE", m.hexdigest())

    # FIXME: set FETCH_DEPENDS based on the schemes set.

    d.set("__fetch", uris)


do_fetch[dirs] = "${INGREDIENTS}"

def do_fetch(d):
    sigfile_changed = False
    for uri in d.get("__fetch"):
        fetch_result = uri.fetch()
        if fetch_result == False:
            return False
        elif isinstance(fetch_result, tuple):
            sigfile = d["__fetch_signatures"]
            sigfile[fetch_result[0]] = fetch_result[1]
            sigfile_changed = True
        else:
            assert fetch_result == True
    if sigfile_changed:
        sigfile.write()
        print "Error: Fetch signatures modified, rebuild needed"
        return False
    return


do_unpack[dirs] = "${SRCDIR}"
do_unpack[cleandirs] = "${SRCDIR}"

def do_unpack(d):
    for uri in d.get("__fetch"):
        if "unpack" in uri.params:
            unpack_cmd = d.get("UNPACK_CMD_%s"%(uri.params["unpack"]))
        else:
            unpack_cmd = None
        if not uri.unpack(unpack_cmd):
            return False
    return


do_patch[dirs] = "${S} ${PATCHDIR}"

def do_patch(d):
    uri = oelite.fetch.patch_init(d)
    for uri in d.get("__fetch"):
        if not "patch" in uri.params:
            continue
        if not uri.patch():
            return False
    return
