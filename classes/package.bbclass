# -*- mode:python; -*-

addtask split after do_fixup
addtask package after do_split before do_build

do_split[cleandirs] = "${PKGD}"
do_split[dirs] = "${PKGD} ${D}"

def do_split(d):
    import glob, errno, stat

    packages = (bb.data.getVar("PACKAGES", d, 1) or "").split()
    if len(packages) < 1:
        bb.error("No packages to build")
        return False

    ddir = bb.data.getVar("D", d, True)
    pkgd = bb.data.getVar("PKGD", d, True)
    pn = bb.data.getVar("PN", d, True)
    packages = bb.data.getVar("PACKAGES", d, True).split()

    # Sanity check PACKAGES for duplicates.
    # move to sanity.bbclass once we have the infrastucture
    package_list = []
    for pkg in packages:
        if pkg in package_list:
            bb.error("%s is listed in PACKAGES multiple times" % pkg)
            continue
        package_list.append(pkg)

    seen = []
    main_is_empty = 1
    main_pkg = bb.data.getVar("PN", d, 1)

    for pkg in package_list:
        localdata = bb.data.createCopy(d)
        root = os.path.join(pkgd, pkg)
        bb.utils.mkdirhier(root)

        bb.data.setVar("PKG", pkg, localdata)

        filesvar = bb.data.getVar("FILES_%s"%(pkg), localdata, True) or ""
        files = filesvar.split()
        for file in files:
            if os.path.isabs(file):
                file = "." + file
            if not os.path.islink(file):
                if os.path.isdir(file):
                    newfiles =  [os.path.join(file,x) for x in os.listdir(file)]
                    if newfiles:
                        files += newfiles
                        continue
            globbed = glob.glob(file)
            if globbed:
                if [ file ] != globbed:
                    if not file in globbed:
                        files += globbed
                        continue
                    else:
                        globbed.remove(file)
                        files += globbed
            if (not os.path.islink(file)) and (not os.path.exists(file)):
                continue
            if file in seen:
                continue
            seen.append(file)
            if os.path.isdir(file) and not os.path.islink(file):
                bb.utils.mkdirhier(os.path.join(root,file))
                os.chmod(os.path.join(root,file), os.stat(file).st_mode)
                continue
            fpath = os.path.join(root,file)
            dpath = os.path.dirname(fpath)
            bb.utils.mkdirhier(dpath)
            ret = bb.utils.copyfile(file, fpath)
            if ret is False or ret == 0:
                raise bb.build.FuncFailed("File population failed")
            if pkg == main_pkg and main_is_empty:
                main_is_empty = 0
        del localdata

    unshipped = []
    for root, dirs, files in os.walk(ddir + "/"):
        for f in files:
            path = os.path.join(root[len(ddir):], f)
            if ("." + path) not in seen:
                unshipped.append(path)

    if unshipped != []:
        bb.note("the following files were installed but not shipped in any package:")
        for f in unshipped:
            bb.note("  " + f)

    for pkg in package_list:
        pkgname = bb.data.getVar("PKG_%s" % pkg, d, 1)
        if pkgname is None:
            bb.data.setVar("PKG_%s" % pkg, pkg, d)

    dangling_links = {}
    pkg_files = {}
    for pkg in package_list:
        dangling_links[pkg] = []
        pkg_files[pkg] = []
        inst_root = os.path.join(ddir, pkg)
        for root, dirs, files in os.walk(inst_root):
            for f in files:
                path = os.path.join(root, f)
                rpath = path[len(inst_root):]
                pkg_files[pkg].append(rpath)
                try:
                    s = os.stat(path)
                except OSError, (err, strerror):
                    if err != errno.ENOENT:
                        raise
                    target = os.readlink(path)
                    if target[0] != "/":
                        target = os.path.join(root[len(inst_root):], target)
                    dangling_links[pkg].append(os.path.normpath(target))

    for pkg in package_list:
        rdepends = bb.utils.explode_deps(
            bb.data.getVar("RDEPENDS_" + pkg, d, 0) or "")

        for l in dangling_links[pkg]:
            found = False
            print "%s contains dangling link %s"%(pkg, l)
            for p in package_list:
                for f in pkg_files[p]:
                    if f == l:
                        found = True
                        print "target found in %s"%(p)
                        if p == pkg:
                            break
                        if not p in rdepends:
                            rdepends.append(p)
                        break
            if found == False:
                bb.note("%s contains dangling symlink to %s" % (pkg, l))
        bb.data.setVar("RDEPENDS_" + pkg, " " + " ".join(rdepends), d)

do_package[dirs] = "${PKGD}"

python do_package () {
    import bb, os

    packages = (d.getVar("PACKAGES", True) or "").split()
    if len(packages) < 1:
        bb.warn(1, "no packages")
        return

    pkgd = d.getVar("PKGD", True)
    deploy_dir = d.getVar("PACKAGE_DEPLOY_DIR", True)
    for package in packages:
        pkg_arch = (d.get("PACKAGE_ARCH_" + package) or
                    d.get("RECIPE_ARCH"))
        pkg_type = (d.get("PACKAGE_TYPE_" + package) or
                    d.get("RECIPE_TYPE"))
        outdir = os.path.join(deploy_dir, pkg_type, pkg_arch)
        pv = d.getVar("PV", True)
        buildhash = d.getVar("TASK_BUILDHASH", False)
        bb.utils.mkdirhier(outdir)
        os.chdir(os.path.join(pkgd, package))
        # FIXME: add error handling for tar command
        os.system("tar cf %s/%s_%s_%s.tar ."%(outdir, package, pv, buildhash))
        srcfile = "%s_%s_%s.tar"%(package, pv, buildhash)
        symlink = "%s/%s_%s.tar"%(outdir, package, pv)
        if os.path.exists(symlink):
            os.remove(symlink)
        os.symlink(srcfile, symlink)
}
