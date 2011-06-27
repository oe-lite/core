# -*- mode:python; -*-

addtask fetch after stage_fixup
addtask unpack after fetch

#
# FIXME: implement a hook for parsing SRC_URI and storing the result
# in __fetcher, and set FETCHER_DEPENDS with required native:* dependencies.
#
# The do_fetch task can then just call d.get("__fetcher") and use that.
#

FETCHER_DEPENDS = ""
CLASS_DEPENDS += "${FETCHER_DEPENDS}"

addhook fetch_init to post_recipe_parse first

def fetch_init(d):
    import oelite.fetch
    uris = []
    schemes = set()
    failed = False
    for src_uri in (d.get("SRC_URI") or "").split():
        try:
            uri = oelite.fetch.OEliteUri(src_uri, d)
            schemes.add(uri.scheme)
            uris.append(uri)
        except oelite.fetch.FetchException as e:
            print e
            failed = True
    if failed:
        print "Bad SRC_URI"
        return False

    # FIXME: set FETCH_DEPENDS based on the schemes set.

    d.set("__fetch", uris)

do_fetch[dirs] = "${INGREDIENTS}"
def do_fetch(d):
    for uri in d.get("__fetch"):
        if not uri.fetch():
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

def do_patch(d):
    uri = oelite.fetch.patch_init(d)
    for uri in d.get("__fetch"):
        if not "patch" in uri.params:
            continue
        if not uri.patch():
            return False
    return
