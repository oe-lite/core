import sys, os
from oebakery import die, err, warn, info, debug
from oelite import InvalidRecipe
import oelite.data


class OEliteRecipe:

    def __init__(self, filename, extend, data, db):
        self.db = db
        self.data = data

        self._datahash = None
        self._srchash = "FOOBAR"
        self._hash = None


        oelite.pyexec.exechooks(self.data, "post_recipe_parse")
        name = data.getVar("PN", 1)
        if not name:
            raise InvalidRecipe("no PN in %s:%s"%(
                    filename, extend))

        version = data.getVar("PV", 1) or "0"
        if "PR" in data:
            version += "-" + data.getVar("PR", 1)

        preference = data.getVar("DEFAULT_PREFERENCE", 1) or "0"
        try:
            preference = int(preference)
        except ValueError, e:
            raise InvalidRecipe("invalid DEFAULT_PREFERENCE=%s in %s:%s"%(
                    preference, filename, extend))

        self.db.add_recipe(filename, extend, name, version, preference)
        recipe_id = self.db.get_recipe_id(filename, extend)

        depends = data.getVar("DEPENDS", 1) or ""
        for depend in depends.split():
            self.db.add_item(depend)
            self.db.add_recipe_depend(recipe_id, depend)

        rdepends = data.getVar("RDEPENDS", 1) or ""
        for rdepend in rdepends.split():
            self.db.add_ritem(rdepend)
            self.db.add_recipe_rdepend(recipe_id, rdepend)

        task_deps = data.getVar("_task_deps", 0)

        tasks = self.data.getVarsWithFlag("task")
        for task in tasks:
            self.db.add_task(recipe_id, task)

        for task in tasks:
            task_id = self.db.get_task_id(recipe_id, task)

            for parent in self.data.getVarFlagSplit(task, "deps"):
                self.db.add_task_parent(task_id, parent, recipe=recipe_id)

            for deptask in self.data.getVarFlagSplit(task, "deptask"):
                self.db.add_task_deptask(task_id, deptask)

            for rdeptask in self.data.getVarFlagSplit(task, "rdeptask"):
                self.db.add_task_rdeptask(task_id, rdeptask)

            for recdeptask in self.data.getVarFlagSplit(task, "recdeptask"):
                self.db.add_task_recdeptask(task_id, recdeptask)

            for recrdeptask in self.data.getVarFlagSplit(task, "recrdeptask"):
                self.db.add_task_recrdeptask(task_id, recrdeptask)

            for recadeptask in self.data.getVarFlagSplit(task, "recadeptask"):
                self.db.add_task_recadeptask(task_id, recadeptask)

            for depends in self.data.getVarFlagSplit(task, "depends"):
                depends_split = depends.split(":")
                if len(depends_split) != 2:
                    err("invalid task 'depends' value "
                        "(valid syntax is item:task): %s"%(depends))
                self.db.add_task_depend(task_id,
                                        depend_item=depends_split[0],
                                        depend_task=depends_split[1])

            if self.data.getVarFlag(task, "nostamp", 0):
                self.db.set_task_nostamp(task_id)

        packages = data.getVar("PACKAGES", 1)
        if not packages:
            warn("no PACKAGES in recipe %s"%name)
            return

        for package in packages.split():

            arch = (self.data.getVar("PACKAGE_ARCH_" + package, True) or
                    self.data.getVar("RECIPE_ARCH", True))
            self.db.add_package(recipe_id, package, arch)
            package_id = self.db.get_package_id(recipe_id, package)

            provides = data.getVar("PROVIDES_" + package, 1) or ""
            for item in provides.split():
                self.db.add_provider(package_id, item)

            rprovides = data.getVar("RPROVIDES_" + package, 1) or ""
            for ritem in rprovides.split():
                self.db.add_rprovider(package_id, ritem)

            depends = data.getVar("DEPENDS_" + package, 1) or ""
            for item in depends.split():
                self.db.add_package_depend(package_id, item)

            rdepends = data.getVar("RDEPENDS_" + package, 1) or ""
            for ritem in rdepends.split():
                self.db.add_package_rdepend(package_id, ritem)

        self.id = recipe_id

        return


    def prepare(self, runq, task):

        data = self.data.createCopy()

        buildhash = self.db.get_runq_task_buildhash(task)
        debug("buildhash=%s"%(repr(buildhash)))
        data.setVar("TASK_BUILDHASH", buildhash)

        deploy_dir = data.getVar("PACKAGE_DEPLOY_DIR", True) 

        recipe_type = data.getVar("RECIPE_TYPE", False)
        
        if recipe_type == "canadian-cross":
            host_arch = data.getVar("HOST_ARCH", True)

        def set_pkgproviders(self_db_get_runq_depend_packages,
                             PKGPROVIDER_, RECDEPENDS):
            recdepends = []

            packages = self_db_get_runq_depend_packages(task) or []
            for package in packages:
                if package in recdepends:
                    continue

                (package_name, package_arch) = self.db.get_package(package)
                filename = self.db.get_runq_package_filename(package)
                recdepends.append(package_name)
                debug("setting %s%s=%s"%(
                        PKGPROVIDER_, package_name, filename))
                data.setVar(PKGPROVIDER_ + package_name, filename)

                if package_arch.startswith("native/"):
                    subdir = "native"
                else:
                    subdir = package_arch.split("/", 1)[0]
                    if recipe_type == "canadian-cross":
                        if package_arch == "cross/%s"%(host_arch):
                            subdir = os.path.join("host", subdir)
                        elif package_arch == "sysroot/%s"%(host_arch):
                            subdir = os.path.join("host", subdir)
                        elif package_arch.startswith("sysroot/%s--"%(host_arch)):
                            subdir = os.path.join("host", subdir)
                        else:
                            subdir = os.path.join("target", subdir)
                data.setVar("PKGSUBDIR_" + package_name, subdir)

            if recdepends:
                debug("setting %s=%s"%(RECDEPENDS, " ".join(recdepends)))
            data.setVar(RECDEPENDS, " ".join(recdepends))

        set_pkgproviders(self.db.get_runq_depend_packages,
                         "PKGPROVIDER_", "RECDEPENDS")

        set_pkgproviders(self.db.get_runq_rdepend_packages,
                         "PKGRPROVIDER_", "RECRDEPENDS")

        return data


    def datahash(self):
        import bb.data
        import hashlib

        if self._datahash:
            return self._datahash

        class StringOutput:
            def __init__(self):
                self.blob = ""
            def write(self, msg):
                self.blob += str(msg)
            def __len__(self):
                return len(self.blob)

        class StringHasher:
            def __init__(self, hasher):
                self.hasher = hasher
            def write(self, msg):
                self.hasher.update(str(msg))
            def __str__(self):
                return self.hasher.hexdigest()

        hasher = StringHasher(hashlib.md5())

        oelite.data.dump(hasher, self.data, pretty=False, nohash=False)

        self._datahash = str(hasher)
        return self._datahash


    def srchash(self):
        if self._srchash:
            return self._srchash
