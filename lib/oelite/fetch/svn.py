import sys
import os
import string
import shutil
import time
import warnings
import hashlib
import oelite.fetch
import pysvn
import tarfile
from oelite.fetch.url import grab

#
# Syntax:
#
# SRC_URI = "svn://host/your/path/to/svn/repo;protocol=http;rev=r42"
# SRC_URI = "svn://host/your/path/to/svn/repo;protocol=https;rev=HEAD"
# SRC_URI = "svn://host/your/path/to/svn/repo;protocol=svn;rev=2012-04-17"
#

#
# SVN fetcher design
# ==============================
#
# In do_fetch
# -----------
#
# The repository is checked out as a working copy under INGREDIENTS.
#
# If using a rev parameter (revision or datetime specification), a signature
# is calculated.
#
# If using a rev parameter and not scmdata=keep, a tarball of the the specific
# revision is stored and will be used instead of a svn checkout when
# available.
#
#
# In do_unpack
# ------------
#
# For non scmdata=keep sources with a rev paramater, the snapshot tarball is
# simply unpacked.  For other svn sources, the .svn directories are copied
# from ingredients to a skeleton source directory tree, and svn update is then
# called to checkout the required revision.
#

class SvnFetcher():

    SUPPORTED_SCHEMES = ("svn")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.SvnFetcher"%(scheme))
        uri.fdepends.append("native:svn")
        self.uri = uri
        try:
            protocol = uri.params["protocol"]
        except KeyError:
            protocol = "svn"
        self.url = "%s://%s"%(protocol, self.uri.location)
        self.wc_name = protocol + "_" + \
            self.uri.location.rstrip("/").translate(string.maketrans("/", "_"))
        self.wc = os.path.join(uri.ingredients, uri.isubdir, "svn",
                               self.wc_name)
        try:
            self.rev = uri.params["rev"]
        except:
            self.rev = "HEAD"
        self.is_head = self.rev == "HEAD"
        if not self.is_head:
            self.signature_name = "svn://" + uri.location
            if protocol != "svn":
                self.signature_name += ";protocol=" + protocol
            self.signature_name += ";rev=" + self.rev
        repo_name = uri.location.rstrip("/").split("/")[-1]
        if "subdir" in uri.params:
            self.dest = uri.params["subdir"]
            if self.dest[-1] == "/":
                self.dest += repo_name
        else:
            self.dest = repo_name
        try:
            self.scmdata_keep = (uri.params["scmdata"] == "keep")
        except KeyError:
            self.scmdata_keep = False
        self.fetch_signatures = d["__fetch_signatures"]
        self.set_signature()
        if not self.is_head and not self.scmdata_keep:
            if self._signature is not None:
                self.localpath = self.snapshot_tarball_path(self.signature())
        return

    def set_signature(self):
        if self.rev == "HEAD":
            warnings.warn("Fetching SVN HEAD breaks source signature handling")
            self._signature = ""
            return
        try:
            self._signature = self.fetch_signatures[self.signature_name]
        except KeyError:
            self._signature = None
        return

    def signature(self):
        if self._signature is None:
            raise oelite.fetch.NoSignature(self.uri, "signature unknown")
        return self._signature

    def has_signature(self):
        return bool(self._signature)

    def get_revision(self):
        try:
            return self._rev
        except:
            pass
        if self.rev == "HEAD":
            self._rev = pysvn.Revision(pysvn.opt_revision_kind.head)
        elif self.rev.startswith("r"):
            self._rev = pysvn.Revision(pysvn.opt_revision_kind.number,
                                      self.rev[1:])
        else: # assuming date/time revision specification
            t = None
            for timefmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                            "%Y-%m-%d w%W", "%Y-%m-%d"):
                try:
                    t = time.strptime(self.rev, timefmt)
                    continue
                except ValueError:
                    pass
            if not t:
                raise Exception("Invalid SVN revision: %s"%(self.rev))
            t = time.mktime(t)
            self._rev = pysvn.Revision(pysvn.opt_revision_kind.date, t)
        return self._rev

    def update_ingredients_wc(self):
        print "Updating ingredients working copy"
        client = pysvn.Client()
        if os.path.exists(self.wc):
            badwc = False
            try:
                status = client.status(self.wc)
                for s in status:
                    if ((not s.is_versioned) or
                        (not s.text_status == pysvn.wc_status_kind.normal) or
                        (not s.prop_status in (pysvn.wc_status_kind.none,
                                               pysvn.wc_status_kind.normal))):
                        badwc = True
                        break
            except pysvn.ClientError:
                badwc = True
            if badwc:
                print "Warning: Deleting bad SVN working copy:", self.wc
                shutil.rmtree(self.wc)
        if not os.path.exists(os.path.dirname(self.wc)):
            os.makedirs(os.path.dirname(self.wc))
        def get_login(real, username, may_save):
            import getpass
            print "Enter SVN credentials for", self.url
            real_stdin = sys.stdin
            username = getpass.getuser()
            try:
                with open("/dev/tty") as tty:
                    sys.stdin = tty
                    username = (raw_input("Username (default '%s'): "%(username))
                                or username)
                    sys.stdin = real_stdin
            except:
                sys.stdin = real_stdin
                print "Error: SVN authorization failed"
                return False, None, None, None
            password = getpass.getpass()
            return True, username, password, True
        client.callback_get_login = get_login
        client.checkout(self.url, self.wc, recurse=True,
                        revision=self.get_revision(), ignore_externals=False)
        return

    def get_ingredients_wc_signature(self):
        print "Computing ingredients working copy signature"
        return svn_signature(self.wc)

    def snapshot_tarball_path(self, signature):
        return "%s_%s.tar.bz2"%(self.wc, signature)

    def save_snapshot_tarball(self, signature):
        print "Generating snapshot tarball"
        tarball = tarfile.open(self.snapshot_tarball_path(signature),
                               mode="w:bz2")
        def exclude_dot_svn(filename):
            return os.path.basename(filename) == ".svn"
        tarball.add(self.wc, arcname=self.dest, exclude=exclude_dot_svn)
        tarball.close()
        return

    def has_snapshot_tarball(self):
        if not self.has_signature():
            return False
        return os.path.exists(self.localpath)

    def fetch_snapshot_tarball(self, urls):
        if not self.has_signature():
            return False
        for url in urls:
            if url[0].endswith("//"):
                mirror_name = "%s_%s.tar.bz2"%(self.wc_name, self.signature())
                url = os.path.join(url[0].rstrip("/"), mirror_name)
            else:
                # only "//" style mirrors for svn snapshots
                continue
            try:
                if grab(url, self.localpath):
                    print "Downloaded snapshot from", url
                    return True
            except Exception, e:
                print "Warning: fetching snapshot %s failed: %s"%(
                    url, e)
        return False

    def fetch(self):
        try_snapshot = (not self.is_head and
                        not self.scmdata_keep and
                        self.has_signature())
        if try_snapshot:
            if self.has_snapshot_tarball():
                print "Using available snapshot tarball"
                return True
            if self.fetch_snapshot_tarball(self.uri.premirrors):
                print "Using fetched snapshot tarball"
                return True
        try:
            self.update_ingredients_wc()
        except Exception, e:
            if not self.is_head:
                if self.scmdata_keep:
                    print "Error: Update of ingredients working copy failed:", e
                    return False
                print "Warning: Update of ingredients working copy failed:", e
                if self.fetch_snapshot_tarball(self.uri.mirrors):
                    return True
                print "Error: SVN fetching failed"
                return False
        if self.is_head:
            if self.os.path.exists(self.wc):
                return True
            else:
                return False
        signature = self.get_ingredients_wc_signature()
        if not self.scmdata_keep:
            self.save_snapshot_tarball(signature)
        if not self.has_signature():
            return (self.signature_name, signature)
        if signature == self.signature():
            return True
        else:
            print "Error: signature mismatch for", str(self.uri)
            print "  Got:     ", signature
            print "  Expected:", self.signature()
            return False

    def clone(self, client, dst):
        print "Cloning to source working copy"
        os.makedirs(dst)
        for root, dirs, files in os.walk(self.wc):
            if ".svn" in dirs:
                dirs.remove(".svn")
                dot_svn_src = os.path.join(root, ".svn")
                dot_svn_dst = os.path.join(dst, root[len(self.wc)+1:], ".svn")
                shutil.copytree(dot_svn_src, dot_svn_dst, symlinks=True)
        client.update(dst, revision=self.get_revision())
        return

    def clean_scmdata(self, wc):
        for root, dirs, files in os.walk(wc):
            if ".svn" in dirs:
                shutil.rmtree(os.path.join(root, ".svn"))
                dirs.remove(".svn")
        return

    def unpack(self, d):
        # Note: when self.localpath is set, this method is not called, but
        # unpacking is instead handled by OEliteUri.unpack method directly.
        client = pysvn.Client()
        self.clone(client, self.dest)
        if not self.scmdata_keep:
            self.clean_scmdata(self.dest)
        return True

    def verify_unpacked(self):
        signature = svn_signature(self.dest)
        if not signature == self.signature():
            print "Error: Invalid snapshot tarball unpacked"
            print "  Got:     ", signature
            print "  Expected:", self.signature()
            return False
        return True


def svn_signature(wc):
    m = hashlib.sha1()
    for root, dirs, files in os.walk(wc):
        if ".svn" in dirs:
            dirs.remove(".svn")
        for filename in files:
            filepath = os.path.join(root, filename)
            stat = os.lstat(filepath)
            m.update(str(stat.st_mode))
            if os.path.islink(filepath):
                m.update(os.readlink(filepath))
            else:
                with open(filepath, "r") as file:
                    m.update(file.read())
    return m.hexdigest()
