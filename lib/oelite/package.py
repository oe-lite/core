import sys, os
from oebakery import die, err, warn, info, debug
import oelite.meta


class OElitePackage:

    def __init__(self, id, name, type, arch, recipe):
        self.id = id
        self.name = name
        self.type = type
        self.arch = arch
        self.recipe = recipe
        self.priority = recipe.priority
        self.version = recipe.version
        return

    def __str__(self):
        return "%s:%s"%(self.type, self.name)
