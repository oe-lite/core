class GitFetcher():

    SUPPORTED_SCHEMES = ("git")

    def __init__(self, uri):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.GitFetcher"%(scheme))
        self.uri = uri
        self.localpath = None
        return

    def fetch(self):
        raise Exception("git fetcher not implemented")
        return False

