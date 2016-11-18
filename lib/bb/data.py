# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
"""
BitBake Data API wrapper for OE-lite
"""

def getVar(var, d, exp=0):
    return d.get(var, exp)
