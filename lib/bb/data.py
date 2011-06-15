# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
"""
BitBake Data API wrapper for OE-lite
"""

import sys
import warnings

def setVar(var, value, d):
    d.set(var, value)

def getVar(var, d, exp=0):
    return d.get(var, exp)

def setVarFlag(var, flag, value, d):
    d.set_flag(var, flag, value)

def getVarFlag(var, flag, d):
    return d.get_flag(var, flag)

def expand(s, d):
    return d.expand(s)

def inherits_class():
    raise Exception("bb.data.inherits_class() not implemented")

def emit_env(o=sys.__stdout__, d=None):
    return d.dump(o=o)

def createCopy(d):
    return d.copy()

def update_data():
    warnings.warn("update_data() is deprecated")
    return
