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
        layer_priority = recipe.meta.get('LAYER_PRIORITY_%s'%(self.name))
        if layer_priority is not None:
            layer_priority = int(layer_priority)
        else:
            layer_priority = recipe.layer_priority
        priority = recipe.meta.get('PRIORITY_%s'%(self.name))
        if priority is None:
            priority = recipe.meta.get('PRIORITY')
        priority = int(priority)
        self.priority = layer_priority + recipe.priority_baseline + priority
        self.version = recipe.version
        self.recdepends = dict()
        for t in ("DEPENDS", "RDEPENDS", "FDEPENDS"):
            self.recdepends[t] = set([])
        return

    def __str__(self):
        return "%s:%s"%(self.type, self.name)

    def get_provides(self):
        provides = self.recipe.get('PROVIDES_' + self.name)
        provides = set((provides or "").split())
        package_type = self.recipe.get('PACKAGE_TYPE_' + self.name)
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
            needed_by='package %s'%(self), ignore_missing=True)
        provides = set()
        for package in packages:
            provides.update(package.get_provides())
        return map(str, provides)

    def set_recdepends(self, deptype, packages):
        assert(deptype in self.recdepends)
        self.recdepends[deptype].update(packages)

    def get_recdepends(self, deptype):
        assert(deptype in self.recdepends)
        return list(self.recdepends[deptype])
