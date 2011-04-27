from collections import MutableMapping
from oelite.parse.expandparse import ExpandParser

class BaseData(MutableMapping):

    def __init__(self):
        #self.expandparser = ExpandParser(self)
        return

    def appendVar(self, var, value, separator=""):
        current = self.getVar(var, 0)
        if current == None:
            self.setVar(var, value)
        else:
            self.setVar(var, current + separator + value)

    def appendVarFlag(self, var, flag, value, separator=""):
        current = self.getVarFlag(var, flag, 0)
        if current == None:
            self.setVarFlag(var, flag, value)
        else:
            self.setVarFlag(var, flag, current + separator + value)

    def prependVar(self, var, value, separator=""):
        current = self.getVar(var, 0)
        if current == None:
            self.setVar(var, value)
        else:
            self.setVar(var, value + separator + current)

    def prependVarFlag(self, var, flag, value, separator=""):
        current = self.getVarFlag(var, flag, 0)
        if current == None:
            self.setVarFlag(var, flag, value)
        else:
            self.setVarFlag(var, flag, value + separator + current)

    def getVar(self, var, expand=1):
        val = self.getVarFlag(var, "", expand)
        return val

    def setVar(self, var, value):
        return self.setVarFlag(var, "", value)

    def expand(self, val, allow_unexpand=False):
        #print "base.expand %s"%(val)
        #self.expandparser.set_allow_unexpand(allow_unexpand)
        expandparser = ExpandParser(self, allow_unexpand)
        if not val:
            return val
        #expval = self.expandparser.expand(val)
        expval = expandparser.expand(val)
        return expval


    #def __contains__(self, var):
    #    val = self.getVar(var, 0)
    #    return val is not None
    #
    #def __getitem__(self, var):
    #    return self.getVar(var, 0)
    #    
    #def __setitem__(self, var, val):
    #    self.setVar(var, val)
    #
    #def __delitem__(self, var):
    #    self.delVar(var)
