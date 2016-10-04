#!/usr/bin/python
import os
import fcntl
import ctypes
import sys

__all__ = ["dup_cloexec", "open_cloexec"]

# uname() -> (sysname, nodename, release, version, machine)
sysname, _, release, _, machine = os.uname()

values = dict()
if (sysname, machine) == ("Linux", "x86_64"):
    # these are supported since at least 2.6.24, so just set them unconditionally
    values['O_CLOEXEC'] = 02000000
    values['F_DUPFD_CLOEXEC'] = 1024+6

# import bb.utils doesn't work when we try to run this by itself (to
# test it), so this just serves to show what one could do, provided
# someone figures out how to make the vercmp_string available.
#
# elif sysname == "FreeBSD":
#     if bb.utils.vercmp_string(release, "8.3") >= 0:
#         values['O_CLOEXEC'] = 0x00100000
#     if bb.utils.vercmp_string(release, "9.2") >= 0:
#         values['F_DUPFD_CLOEXEC'] = 17

def dup_cloexec(fd):
    return fcntl.fcntl(fd, F_DUPFD_CLOEXEC, 0)

def open_cloexec(filename, flag, mode=0777):
    return os.open(filename, flag | O_CLOEXEC, mode)

def set_cloexec(fd):
    fcntl.fcntl(fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)
    return fd

def dup_cloexec_fallback(fd):
    return set_cloexec(os.dup(fd))

def open_cloexec_fallback(filename, flag, mode=0777):
    return set_cloexec(os.open(filename, flag, mode))

if hasattr(os, "O_CLOEXEC"):
    O_CLOEXEC = os.O_CLOEXEC
else:
    try:
        O_CLOEXEC = values["O_CLOEXEC"]
    except KeyError:
        open_cloexec = open_cloexec_fallback

if hasattr(fcntl, "F_DUPFD_CLOEXEC"):
    F_DUPFD_CLOEXEC = fcntl.F_DUPFD_CLOEXEC
else:
    try:
        F_DUPFD_CLOEXEC = values["F_DUPFD_CLOEXEC"]
    except KeyError:
        dup_cloexec = dup_cloexec_fallback


def has_cloexec(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    return (flags & fcntl.FD_CLOEXEC) != 0

def test_open_cloexec():
    fd = open_cloexec("/dev/null", os.O_RDONLY)
    assert(has_cloexec(fd))
    os.close(fd)
    fd = open_cloexec("/dev/null", os.O_WRONLY)
    assert(has_cloexec(fd))
    os.close(fd)

def test_dup_cloexec():
    fd = dup_cloexec(sys.stdin.fileno())
    assert(has_cloexec(fd))
    os.close(fd)


if __name__ == "__main__":
    test_open_cloexec()
    test_dup_cloexec()
