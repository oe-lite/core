import urlgrabber
import os.path
import bb.utils

class UrlFetcher():

    SUPPORTED_SCHEMES = ("http", "https", "ftp")

    def __init__(self, uri):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.UrlFetcher"%(
                    uri.scheme))
        self.url = "%s://%s"%(uri.scheme, uri.location)
        try:
            isubdir = uri.params["isubdir"]
        except KeyError:
            isubdir = uri.isubdir
        
        self.localpath = os.path.join(uri.ingredients, isubdir,
                                      os.path.basename(uri.location))
        self.uri = uri
        return

    def fetch(self):
        print "Fetching", self.url
        localdir = os.path.dirname(self.localpath)
        if not os.path.exists(localdir):
            bb.utils.mkdirhier(localdir)
        try:
            f = urlgrabber.urlgrab(self.url, self.localpath, reget="simple")
        except urlgrabber.grabber.URLGrabError as e:
            if not e[0] == 14 and e[1].startswith("HTTP Error 416"):
                return False
            f = urlgrabber.urlgrab(self.url, self.localpath)
        return f == self.localpath
