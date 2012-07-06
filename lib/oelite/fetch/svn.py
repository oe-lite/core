import sys
import os
import string
import shutil
import time
import warnings
import hashlib
import oelite.fetch

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
# Adding SRC_URI mirror support should be done using tarballs. Need to
# find out how to handle the .svn dirs in that case.  Perhaps add a
# parameter for keeping the .svn dirs after unpacking, and if not
# kept, the tarballs can be done from an svn export, while if keepig
# .svn dirs is needed, the .svn dirs needs to be packaged together
# with the src.  In that case, care must be taken to not use a tarball
# without .svn dirs for a recipe that needs .svn dirs.
#
# In do_unpack
# ------------
#
# Symbolic link from .svn dir in working copy in INGREDIENTS, and then
# checkout of the proper version.
#

class SvnFetcher():

    SUPPORTED_SCHEMES = ("svn")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.SvnFetcher"%(scheme))
        uri.fdepends.append("native:svn")
        self.uri = uri
        self.wc = os.path.join(
            uri.ingredients, uri.isubdir, "svn",
            self.uri.location.rstrip("/").translate(string.maketrans("/", "_")))
        try:
            protocol = uri.params["protocol"]
        except KeyError:
            protocol = "svn"
        self.url = "%s://%s"%(protocol, self.uri.location)
        try:
            self.rev = uri.params["rev"]
        except:
            self.rev = "HEAD"
        if self.rev != "HEAD":
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
        return

    def signature(self):
        if self.rev == "HEAD":
            warnings.warn("Fetching SVN HEAD breaks source signature handling")
            return ""
        try:
            self._signature = self.fetch_signatures[self.signature_name]
        except KeyError:
            raise oelite.fetch.NoSignature(self.uri, "signature unknown")
        return self._signature

    def get_revision(self):
        try:
            return self._rev
        except:
            pass
        import pysvn
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

    def fetch(self):
        import pysvn
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
        try:
            client.checkout(self.url, self.wc, recurse=True,
                        revision=self.get_revision(), ignore_externals=False)
        except:
            print "Error: SVN authorization failed"
            return False
        if self.rev == "HEAD":
            return True
        m = hashlib.sha1()
        for root, dirs, files in os.walk(self.wc):
            if ".svn" in dirs:
                dirs.remove(".svn")
            for filename in files:
                m.update(open(os.path.join(root, filename), "r").read())
        signature = m.hexdigest()
        if not "_signature" in dir(self):
            return (self.signature_name, signature)
        return signature == self._signature

    def unpack(self, d):
        import pysvn
        client = pysvn.Client()
        os.makedirs(self.dest)
        os.symlink(os.path.join(self.wc, ".svn"),
                   os.path.join(self.dest, ".svn"))
        client.update(self.dest, revision=self.get_revision())
        if not self.scmdata_keep:
            os.unlink(os.path.join(self.dest, ".svn"))
        return True
