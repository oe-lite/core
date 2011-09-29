import oelite.fetch
import bb.utils
import os
import urlgrabber
import hashlib

class UrlFetcher():

    SUPPORTED_SCHEMES = ("http", "https", "ftp")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.UrlFetcher"%(
                    uri.scheme))
        self.url = "%s://%s"%(uri.scheme, uri.location)
        try:
            isubdir = uri.params["isubdir"]
        except KeyError:
            isubdir = uri.isubdir
        self.localname = os.path.basename(uri.location)
        self.localpath = os.path.join(uri.ingredients, isubdir, self.localname)
        self.signatures = d.get("FILE") + ".sig"
        self.uri = uri
        self.fetch_signatures = d["__fetch_signatures"]
        return

    def signature(self):
        try:
            self._signature = self.fetch_signatures[self.localname]
            return self._signature
        except KeyError:
            raise oelite.fetch.NoSignature(self.uri, "signature unknown")

    def grab(self, url, reget=None):
        print "grabbing %s"%(url)
        if reget:
            try:
                return urlgrabber.urlgrab(url, self.localpath, reget=reget)
            except urlgrabber.grabber.URLGrabError as e:
                print 'URLGrabError %i: %s' % (e.errno, e.strerror)
                if not (e[0] == 14 and e[1].startswith("HTTP Error 416")):
                    return None
        try:
            return urlgrabber.urlgrab(url, self.localpath)
        except urlgrabber.grabber.URLGrabError as e:
            print 'URLGrabError %i: %s' % (e.errno, e.strerror)
        return None

    def fetch(self):
        localdir = os.path.dirname(self.localpath)
        if not os.path.exists(localdir):
            bb.utils.mkdirhier(localdir)
        url = self.url
        while url:
            if os.path.exists(self.localpath):
                if "_signature" in dir(self):
                    m = hashlib.sha1()
                    m.update(open(self.localpath, "r").read())
                    if self._signature == m.hexdigest():
                        return True
                f = self.grab(url, reget="simple")
            else:
                f = self.grab(url)
            if f:
                break
            url = self.uri.alternative_mirror()
        if not f or f != self.localpath:
            return False
        m = hashlib.sha1()
        m.update(open(self.localpath, "r").read())
        signature = m.hexdigest()
        if not "_signature" in dir(self):
            return (self.localname, signature)
        return signature == self._signature
