#
# General packaging help functions
#

addtask split after do_install
addtask fixup after do_split
#addtask fixup_qa after do_fixup before do_qa
addtask package after do_fixup before do_build
#addtask package_qa after do_package before do_qa
addtask rfixup after do_split
#addtask fixup_qa after do_rfixup before do_qa
addtask rpackage after do_rfixup before do_build
#addtask rpackage_qa after do_rpackage before do_qa


#
# Package functions suitable for inclusion in *_FUNCS
#

python package_split () {
	import bb, glob, errno, re, stat

	workdir = bb.data.getVar('WORKDIR', d, True)
	ddir = bb.data.getVar('D', d, True)
	pkgd = bb.data.getVar('PKGD', d, True)
	pn = bb.data.getVar('PN', d, True)
	packages = bb.data.getVar('PACKAGES', d, True).split()
	
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
	main_pkg = bb.data.getVar('PN', d, 1)
	
	for pkg in package_list:
		localdata = bb.data.createCopy(d)
		root = os.path.join(pkgd, pkg)
		bb.mkdirhier(root)
	
		bb.data.setVar('PKG', pkg, localdata)
		overrides = bb.data.getVar('OVERRIDES', localdata, True)
		if not overrides:
			raise bb.build.FuncFailed('OVERRIDES not defined')
		bb.data.setVar('OVERRIDES', overrides + ':' + pkg, localdata)
		bb.data.update_data(localdata)
	
		filesvar = bb.data.getVar('FILES', localdata, True) or ""
		files = filesvar.split()
		for file in files:
			if os.path.isabs(file):
				file = '.' + file
			if not os.path.islink(file):
				if os.path.isdir(file):
					newfiles =  [ os.path.join(file,x) for x in os.listdir(file) ]
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
				bb.mkdirhier(os.path.join(root,file))
				os.chmod(os.path.join(root,file), os.stat(file).st_mode)
				continue
			fpath = os.path.join(root,file)
			dpath = os.path.dirname(fpath)
			bb.mkdirhier(dpath)
			ret = bb.copyfile(file, fpath)
			if ret is False or ret == 0:
				raise bb.build.FuncFailed("File population failed")
			if pkg == main_pkg and main_is_empty:
				main_is_empty = 0
		del localdata
	
	unshipped = []
	for root, dirs, files in os.walk(ddir + '/'):
		for f in files:
			path = os.path.join(root[len(ddir):], f)
			if ('.' + path) not in seen:
				unshipped.append(path)
	
	if unshipped != []:
		bb.note("the following files were installed but not shipped in any package:")
		for f in unshipped:
			bb.note("  " + f)
	
	for pkg in package_list:
		pkgname = bb.data.getVar('PKG_%s' % pkg, d, 1)
		if pkgname is None:
			bb.data.setVar('PKG_%s' % pkg, pkg, d)
	
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
					if target[0] != '/':
						target = os.path.join(root[len(inst_root):], target)
					dangling_links[pkg].append(os.path.normpath(target))
	
	for pkg in package_list:
		rdepends = bb.utils.explode_deps(bb.data.getVar('RDEPENDS_' + pkg, d, 0) or "")
	
		for l in dangling_links[pkg]:
			found = False
			bb.debug(1, "%s contains dangling link %s" % (pkg, l))
			for p in package_list:
				for f in pkg_files[p]:
					if f == l:
						found = True
						bb.debug(1, "target found in %s" % p)
						if p == pkg:
							break
						if not p in rdepends:
							rdepends.append(p)
						break
			if found == False:
				bb.note("%s contains dangling symlink to %s" % (pkg, l))
		bb.data.setVar('RDEPENDS_' + pkg, " " + " ".join(rdepends), d)
}
package_split[dirs] = "${D}"


def package_clone(packages, dstdir, d):
	pkgd = bb.data.getVar('PKGD', d, 1)

	for pkg in packages:
		src = os.path.join(pkgd, pkg)
		dst = os.path.join(dstdir, pkg)
		bb.mkdirhier(dstdir)
		# FIXME: rewrite to use python function instead of os.system
		os.system('cp -pPR %s/ %s'%(src, dst))


python stage_package_clone () {
	pkgd_stage = bb.data.getVar('PKGD_STAGE', d, True)
	packages = (bb.data.getVar('PACKAGES', d, True) or "").split()
	package_clone(packages, pkgd_stage, d)
}
stage_package_clone[cleandirs] = '${PKGD_STAGE}'
stage_package_clone[dirs] = '${PKGD_STAGE} ${PKGD}'


target_package_clone[cleandirs] = '${PKGD_TARGET}'
target_package_clone[dirs] = '${PKGD_TARGET} ${PKGD}'

python target_package_clone () {
	pkgd_target = bb.data.getVar('PKGD_TARGET', d, True)
	packages = (bb.data.getVar('RPACKAGES', d, True) or "").split()
	package_clone(packages, pkgd_target, d)
}


SPLIT_FUNCS = "\
# package_split_locales\
 package_split\
# package_shlibs\
# package_pkgconfig\
# package_depchains\
"
# FIXME: package_pkgconfig should be dynamically added to
# SPLIT_FUNCS by pkgconfig.bbclass


do_split[cleandirs] = "${PKGD}"
do_split[dirs] = "${PKGD} ${D}"

python do_split () {
	packages = (bb.data.getVar('PACKAGES', d, 1) or "").split()
	if len(packages) < 1:
		bb.error("No packages to build")
		return

	for f in (bb.data.getVar('SPLIT_FUNCS', d, 1) or '').split():
		bb.build.exec_func(f, d)
}


FIXUP_FUNCS = "\
stage_package_clone \
#stage_package_rpath \
#stage_package_shlibs \
#stage_package_pkgconfig \
stage_package_fixup"
# FIXME: stage_package_clone should re-use perform_packagecopy from
# openembedded package.bbclass

# FIXME: stage_package_pkgconfig should be dynamically added to
# SPLIT_FUNCS by pkgconfig.bbclass


do_fixup[cleandirs] = "${PKGD_STAGE}"
do_fixup[dirs] = "${PKGD_STAGE} ${PKGD}"

python do_fixup () {
	stage_packages = (bb.data.getVar('PACKAGES', d, 1) or "").split()
	if len(stage_packages) < 1:
		bb.debug(1, "No stage packages")
		return

	for f in (bb.data.getVar('FIXUP_FUNCS', d, 1) or '').split():
		if not bb.data.getVarFlag(f, 'dirs', d):
			bb.data.setVarFlag(f, 'dirs', '${PKGD_STAGE}', d)
		bb.build.exec_func(f, d)
}


do_package[dirs] = "${PKGD_STAGE}"

python do_package () {
	import bb, os

	stage_packages = (bb.data.getVar('PACKAGES', d, 1) or "").split()
	if len(stage_packages) < 1:
		bb.debug(1, "No stage packages")
		return

	pkgd_stage = bb.data.getVar('PKGD_STAGE', d, True)
	deploy_dir = bb.data.getVar('STAGE_DEPLOY_DIR', d, True)
	for pkg in stage_packages:
		pkg_arch = bb.data.getVar('PACKAGE_ARCH_%s'%pkg, d, True) or bb.data.getVar('RECIPE_ARCH', d, True)
		outdir = os.path.join(deploy_dir, pkg_arch)
		pv = bb.data.getVar('EPV', d, True)
		bb.mkdirhier(outdir)
		basedir = os.path.dirname(pkg_arch)
		# FIXME: rewrite to use python functions instead of os.system
		os.system('mv %s %s'%(pkg, basedir))
		# FIXME: add error handling for tar command
		os.system('tar cf %s/%s-%s.tar %s'%(outdir, pkg, pv, basedir))
		# FIXME: rewrite to use python functions instead of os.system
		os.system('mv %s %s'%(basedir, pkg))
}


RFIXUP_FUNCS = "\
target_package_clone \
#target_package_rpath \
#target_package_shlibs \
#target_package_pkgconfig \
"
# FIXME: target_package_clone should re-use perform_packagecopy from
# openembedded package.bbclass

# FIXME: target_package_pkgconfig should be dynamically added to
# SPLIT_FUNCS by pkgconfig.bbclass


do_rfixup[cleandirs] = "${PKGD_TARGET}"

python do_rfixup () {
	packages = (bb.data.getVar('RPACKAGES', d, 1) or "").split()
	if not packages:
		bb.note("No target packages")
		return

	for f in (bb.data.getVar('RFIXUP_FUNCS', d, 1) or '').split():
		bb.build.exec_func(f, d)
}


do_rpackage[dirs] = "${PKGD_TARGET}"

python do_rpackage () {
	import bb, os

	packages = (bb.data.getVar('RPACKAGES', d, 1) or "").split()
	if not packages:
		bb.note("No target packages")
		return

	pkgd_target = bb.data.getVar('PKGD_TARGET', d, True)
	deploy_dir = bb.data.getVar('TARGET_DEPLOY_DIR', d, True)
	for pkg in packages:
		pkg_arch = bb.data.getVar('PACKAGE_ARCH_%s'%pkg, d, True) or bb.data.getVar('RECIPE_ARCH', d, True)
		outdir = os.path.join(deploy_dir, pkg_arch)
		pv = bb.data.getVar('EPV', d, True)
		bb.mkdirhier(outdir)
		basedir = os.path.dirname(pkg_arch)
		os.chdir(pkg)
		# FIXME: add error handling for tar command
		os.system('tar cf %s/%s-%s.tar .'%(outdir, pkg, pv))
		os.chdir('..')
}
