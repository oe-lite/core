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
