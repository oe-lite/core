import os.path
import bb.utils

class LocalFetcher():

    SUPPORTED_SCHEMES = ("file")

    def __init__(self, uri):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.UrlFetcher"%(scheme))
        self.uri = uri
        self.localpath = uri.location
        if not os.path.isabs(self.localpath):
            filespath = uri.filespath
            if filespath:
                self.localpath = bb.utils.which(filespath, self.localpath)
            if not self.localpath:
                filesdir = uri.files
                if filesdir:
                    self.localpath = os.path.join(filesdir, path)
        return

    def fetch(self):
        return True
