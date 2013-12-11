import oelite.fetch
import oelite.path
import os
import hashlib

class LocalFetcher():

    SUPPORTED_SCHEMES = ("file")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.UrlFetcher"%(scheme))
        self.uri = uri
        if os.path.isabs(uri.location):
            if not os.path.exists(uri.location):
                raise oelite.fetch.LocalFileNotFound(self.uri, "file not found")
            self.localpath = uri.location
            d.set_input_mtime(self.localpath,
                              mtime=os.path.getmtime(self.localpath))
        else:
            self.localpath = oelite.path.which(d.get("FILESPATH_EXISTS"),
                                               uri.location)
            if not self.localpath:
                raise oelite.fetch.LocalFileNotFound(self.uri, "file not found")
            d.set_input_mtime(uri.location, d.get("FILESPATH"),
                              mtime=os.path.getmtime(self.localpath))
        return

    def signature(self):
        try:
            return self._signature
        except AttributeError:
            pass
        m = hashlib.sha1()
        m.update(open(self.localpath, "r").read())
        self._signature = m.digest()
        return self._signature
