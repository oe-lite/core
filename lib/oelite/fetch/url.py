import oelite.fetch
import oelite.util
import os
import hashlib
import subprocess
from oebakery import die, err, warn, info, debug

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

    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    cmd = ['wget', '-t', str(retry), '-T', str(timeout), psvftp, '--no-check-certificate', '--progress=dot:mega', '-v', url, '-O', filename]

    returncode = subprocess.call(cmd, env=env)

    if returncode != 0:
        err("Error %s %d" % (cmd, returncode))
        return False

    if not os.path.exists(filename):
        err("The fetch command returned success for url %s but %s doesn't exist?!" % (url, filename))
        return False

    if os.path.getsize(filename) == 0:
        os.remove(filename)
        err("The fetch of %s resulted in a zero size file?! Deleting and failing since this isn't right." % (url))
        return False

    return True
