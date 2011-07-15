from collections import MutableMapping
import os

class SignatureFile(MutableMapping):

    def __init__(self, filename):
        self.filename = filename
        self.signatures = {}
        if os.path.exists(filename):
            with open(self.filename, "r") as sigfile:
                for sigline in sigfile:
                    signature, localname = sigline.strip().split(None, 1)
                    self.signatures[localname] = signature

    def __getitem__(self, key): # required by Mapping
        return self.signatures[key]

    def __setitem__(self, key, value): # required by MutableMapping
        self.signatures[key] = value
        return value

    def __delitem__(self, key): # required by MutableMapping
        del self.signatures[key]
        return

    def __len__(self): # required by Sized
        return len(self.signatures)

    def __iter__(self): # required by Iterable
        return self.signatures.__iter__()

    def write(self):
        localnames = self.signatures.keys()
        localnames.sort()
        with open(self.filename, "w") as sigfile:
            for localname in localnames:
                sigfile.write("%s  %s\n"%(self.signatures[localname],
                                          localname))
