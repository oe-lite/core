# Low-level signal handling stuff that we unfortunately may need to
# worry about.

from __future__ import absolute_import

import signal

# The Python runtime sets the signal disposition for SIGPIPE to
# SIG_IGN. Unfortunately, such a setting is preserved across both
# fork() and execve(), so unless a spawned program itself takes steps
# to set it back to SIG_DFL (and I know that bash does not), this will
# affect the entire subprocess tree. There may be programs which
# (probably unknowingly) rely on SIGPIPE resulting in the default
# action of terminating the process.  There are certainly no programs
# that expect to started with SIG_IGN for SIGPIPE - if they want to
# get -EPIPE instead of the signal, they do the signal(2) call
# themselves. I haven't seen any problems that can directly be
# attributed to this, but that doesn't mean there haven't been any,
# since errors like these would presumably be extremely hard to
# debug. In any case, this is the right thing to do. This is usable as
# a preexec_fn in a subprocess.Popen() call.
#
# initsigs() in CPython also munges with SIGXFZ and SIGXFSZ, so handle
# them as well - essentially, the below is a Python2 port of Python3's
# _Py_RestoreSignals.
def restore_defaults():
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    if hasattr(signal, "SIGXFZ"):
        signal.signal(signal.SIGXFZ, signal.SIG_DFL)
    if hasattr(signal, "SIGXFSZ"):
        signal.signal(signal.SIGXFSZ, signal.SIG_DFL)

def test_restore():
    import os
    import subprocess
    import errno

    PIPE=subprocess.PIPE
    sub = subprocess.Popen(["yes"], stdout=PIPE, stderr=PIPE)
    # Force a broken pipe.
    sub.stdout.close()
    err = sub.stderr.read()
    # This should terminate with a write error; we assume that 'yes'
    # is so well-behaved that it both exits with a non-zero exit code
    # as well as prints an error message containing strerror(errno).
    ret = sub.wait()
    assert(ret > 0)
    assert(os.strerror(errno.EPIPE) in err)

    sub = subprocess.Popen(["yes"], stdout=PIPE, stderr=PIPE, preexec_fn = restore_defaults)
    # Force a broken pipe.
    sub.stdout.close()
    err = sub.stderr.read()
    # This should terminate due to SIGPIPE, and not get a chance to write to stderr.
    ret = sub.wait()
    assert(ret == -signal.SIGPIPE)
    assert(err == "")

if __name__ == "__main__":
    # To run:
    # meta/core/lib$ python -m oelite.signal
    test_restore()
