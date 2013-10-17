import os

TOPDIR = os.getcwd()


def init(topdir):
    global TOPDIR
    TOPDIR = topdir


def relpath(path):
    """Return a relative version of paths compared to TOPDIR."""
    global TOPDIR
    if path.startswith(TOPDIR):
        return path[len(TOPDIR):].lstrip("/")
    return path


def which(path, filename, pathsep=os.pathsep):
    """Given a search path, find file."""
    if isinstance(path, basestring):
        path = path.split(pathsep)
    for p in path:
        f = os.path.join(p, filename)
        if os.path.exists(f):
            return os.path.abspath(f)
    return '' # TODO: change to None, and fixup the breakage it causes
