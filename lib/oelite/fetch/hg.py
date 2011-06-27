class HgFetcher():

    SUPPORTED_SCHEMES = ("hg")

    def __init__(self, uri):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.HgFetcher"%(scheme))
        self.uri = uri
        self.localpath = None
        return

    def fetch(self):
        return False

