class HgFetcher():

    SUPPORTED_SCHEMES = ("hg")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.HgFetcher"%(scheme))
        self.uri = uri
        self.localpath = None
        return

    def signature(self):
        return ""

    def fetch(self):
        raise Exception("hg fetcher not implemented")
        return False

