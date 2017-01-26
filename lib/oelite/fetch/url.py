import oelite.fetch
import oelite.util
import os
import hashlib
import subprocess
from oebakery import die, err, warn, info, debug
import tempfile
import errno

class UrlFetcher():

    SUPPORTED_SCHEMES = ("http", "https", "ftp")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.UrlFetcher"%(
                    uri.scheme))
        self.url = "%s://%s"%(uri.scheme, uri.location)
        self.localname = os.path.basename(uri.location)
        self.localpath = os.path.join(uri.ingredients, uri.isubdir,
                                      self.localname)
        self.signatures = d.get("FILE") + ".sig"
        self.uri = uri
        self.fetch_signatures = d["__fetch_signatures"]
        self.proxies = self.get_proxies(d)
        self.passive_ftp = self.get_passive_ftp(d)
        return

    def signature(self):
        try:
            self._signature = self.fetch_signatures[self.localname]
            return self._signature
        except KeyError:
            raise oelite.fetch.NoSignature(self.uri, "signature unknown")

    def fetch(self):
        localdir = os.path.dirname(self.localpath)
        oelite.util.makedirs(localdir)

        if os.path.exists(self.localpath):
            if "_signature" in dir(self):
                signature = self.localsignature()
                if signature == self._signature:
                    return True
            print "Removing unverifiable ingredient:", \
                os.path.join(self.uri.isubdir, self.localname)
            os.unlink(self.localpath)

        grabbed = False
        for url in self.uri.premirrors + [self.url] + self.uri.mirrors:
            assert not os.path.exists(self.localpath)
            if not isinstance(url, basestring):
                url = "".join(url)
            if not self.uri.allow_url(url):
                print "Skipping", url
                continue
            if grab(url, self.localpath, proxies=self.proxies, passive_ftp=self.passive_ftp):
                if self.grabbedsignature():
                    grabbed = True
                    break
            if os.path.exists(self.localpath):
                print "Removing ingredient littering:", \
                    os.path.join(self.uri.isubdir, self.localname)
                os.unlink(self.localpath)
        if not grabbed:
            return False
        assert os.path.exists(self.localpath)
        return self.grabbedsignature()

    def grabbedsignature(self):
        signature = self.localsignature()
        if not "_signature" in dir(self):
            return (self.localname, signature)
        if signature != self._signature:
            print "Ingredient signature mismatch:", \
                os.path.join(self.uri.isubdir, self.localname)
            print "  expected: %s"%self._signature
            print "  obtained: %s"%signature
            return False
        else:
            return True

    def localsignature(self):
        m = hashlib.sha1()
        m.update(open(self.localpath, "r").read())
        return m.hexdigest()

    def get_proxies(self, d):
        proxies = {}
        for v in ("http_proxy", "ftp_proxy", "https_proxy"):
            proxy = d.get(v)
            if proxy:
                proxies[v] = proxy
        return proxies

    def get_passive_ftp(self, d):
        val = d.get("DISABLE_FTP_EXTENDED_PASSIVE_MODE")
        if val == "1":
            return False
        return True




def grab(url, filename, timeout=120, retry=5, proxies=None, passive_ftp=True):
    print "Grabbing", url

    if proxies:
        env = os.environ.copy()
        env.update(proxies)
    else:
        env = None # this is the default, uses a copy of the current environment

    if passive_ftp:
        psvftp = '--passive-ftp'
    else:
        psvftp = '--no-passive-ftp'

    d = os.path.dirname(filename)
    f = os.path.basename(filename)
    if not os.path.exists(d):
        os.makedirs(d)

    # Use mkstemp to create and open a guaranteed unique file. We use
    # the file descriptor as wget's stdout. We must download to the
    # actual ingredient dir rather than e.g. /tmp to ensure that we
    # can do a link(2) call without encountering EXDEV.
    (fd, dl_tgt) = tempfile.mkstemp(prefix = f + ".", dir = d)
    # Unfortunately, mkstemp() uses mode 0o600 when opening the file,
    # but we'd rather have used 0o644. So we get to do a little syscall
    # dance, yay.
    mask = os.umask(0o022)
    os.fchmod(fd, 0o644 & ~mask)
    os.umask(mask)

    cmd = ['wget', '-t', str(retry), '-T', str(timeout), psvftp, '--no-check-certificate', '--progress=dot:mega', '-v', url, '-O', '-']

    try:
        returncode = subprocess.call(cmd, env=env, stdout=fd)

        if returncode != 0:
            err("Error %s %d" % (cmd, returncode))
            return False

        if os.fstat(fd).st_size == 0:
            err("The fetch of %s resulted in a zero size file?! Failing since this isn't right." % (url))
            return False

        # We use link(2) rather than rename(2), since the latter would
        # replace an existing target. Although that's still done
        # atomically and the new file should be identical to the old,
        # it's better that once created, the target dentry is
        # "immutable". For example, there might be some code that,
        # when opening a file, first does a stat(2), then actually
        # opens the file, and then does an fstat() and compares the
        # inode numbers. We don't want such code to fail. It's also
        # slightly simpler that we need to do an unlink(2) on all exit
        # paths.
        try:
            os.link(dl_tgt, filename)
        except OSError as e:
            if e.errno == errno.EEXIST:
                # Some other fetcher beat us to it, signature checking
                # should ensure we don't end up using a wrong
                # file. But do make a note of this in the log file so
                # that we can see that the races do occur, and that
                # this works as intended.
                info("Fetching %s raced with another process - this is harmless" % url)
                pass
            else:
                err("os.link(%s, %s) failed: %s", dl_tgt, filename, str(e))
                return False
    finally:
        # Regardless of how all of the above went, we have to delete
        # the temporary dentry and close the file descriptor. We do
        # not wrap these in ignoreall-try-except, since something is
        # really broken if either fails (in particular, subprocess is
        # not supposed to close the fd we give it; it should only dup2
        # it to 1, and then close the original _in the child_).
        os.unlink(dl_tgt)
        os.close(fd)


    return True
