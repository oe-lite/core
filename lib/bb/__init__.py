import bb.data
import bb.utils

import oebakery

def plain(*args):
    oebakery.info(" ".join(args))

def debug(*args):
    oebakery.debug(" ".join(args))

def note(*args):
    oebakery.info(" ".join(args))

def warn(*args):
    oebakery.warn(" ".join(args))

def error(*args):
    oebakery.err(" ".join(args))

def fatal(*args):
    oebakery.die(" ".join(args))

__all__ = [
    "data", "utils",
    "plain", "debug", "note", "warn", "error", "fatal",
    ]
