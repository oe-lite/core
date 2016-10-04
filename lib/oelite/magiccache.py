import magic

class OEliteMagic:

    def __init__(self, flags, filename):
        self.refs = 1
        self.magic  = magic.open(flags)
        self.filename = filename
        self.magic.load(self.filename)

    def get(self):
        self.refs += 1
        return self

    def file(self, filename):
        return self.magic.file(filename)

    def descriptor(self, fd):
        return self.magic.descriptor(fd)

    def close(self):
        self.refs -= 1
        if self.refs == 0:
            self.magic.close()
            self.magic = None


cache = dict()

def open(flags = magic.MAGIC_NONE, filename=None):
    t = (flags,filename)
    if t not in cache:
        cache[t] = OEliteMagic(flags, filename)
    return cache[t].get()

# Drop the reference held by the cache dict - existing instances
# continue to be valid.
def clear_cache():
    for f in cache.keys():
        cache[f].close()
        del cache[f]
