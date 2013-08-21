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

    def get_provides(self):
        provides = self.recipe.get('PROVIDES_%s'%(self.name))
        provides = set((provides or "").split())
        package_type = self.recipe.get('PACKAGE_TYPE_%s'%(self.name))
        if package_type:
            provides.add('%s:%s'%(package_type, self.name))
        else:
            provides.add(self.name)
        return provides

    def get_recprovides(self, deptype, get_depends):
        depends = self.recipe.get('%s_%s'%(deptype, self.name))
        if not depends:
            return []
        if (deptype == 'RDEPENDS' and
            self.type in ('native', 'cross', 'sdk-cross')):
            return []
        depends = (depends or "").split()
        packages = get_depends(
            self.type, depends, deptype, rec_deptype=deptype,
            needed_by='package %s'%(self))
        provides = set()
        for package in packages:
            provides.update(package.get_provides())
        return map(str, provides)
