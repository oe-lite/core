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


ldconfig_postinst_fragment() {
if [ x"$D" = "x" ]; then
	if [ -e /etc/ld.so.conf ] ; then
		[ -x /sbin/ldconfig ] && /sbin/ldconfig
	fi
fi
}

SHLIBSDIR = "${STAGING_DIR_HOST}/shlibs"

python package_do_shlibs() {
	import os, re, os.path

	exclude_shlibs = bb.data.getVar('EXCLUDE_FROM_SHLIBS', d, 0)
	if exclude_shlibs:
		bb.debug(1, "not generating shlibs")
		return

	lib_re = re.compile("^lib.*\.so")
	libdir_re = re.compile(".*/lib$")

	packages = bb.data.getVar('PACKAGES', d, 1)

	workdir = bb.data.getVar('WORKDIR', d, 1)
	if not workdir:
		bb.error("WORKDIR not defined")
		return

	ver = bb.data.getVar('PV', d, 1)
	if not ver:
		bb.error("PV not defined")
		return

	pkgd = bb.data.getVar('PKGD', d, 1)

	shlibs_dir = bb.data.getVar('SHLIBSDIR', d, 1)
	bb.mkdirhier(shlibs_dir)

	pstageactive = bb.data.getVar('PSTAGING_ACTIVE', d, True)
	if pstageactive == "1":
		lf = bb.utils.lockfile(bb.data.expand("${STAGING_DIR}/staging.lock", d))

	if bb.data.getVar('PACKAGE_SNAP_LIB_SYMLINKS', d, True) == "1":
		snap_symlinks = True
	else:
		snap_symlinks = False

	if (bb.data.getVar('USE_LDCONFIG', d, True) or "1") == "1":
		use_ldconfig = True
	else:
		use_ldconfig = False

	needed = {}
	private_libs = bb.data.getVar('PRIVATE_LIBS', d, 1)
	for pkg in packages.split():
		needs_ldconfig = False
		bb.debug(2, "calculating shlib provides for %s" % pkg)

		needed[pkg] = []
		sonames = list()
		top = os.path.join(pkgd, pkg)
		renames = []
		for root, dirs, files in os.walk(top):
			for file in files:
				soname = None
				path = os.path.join(root, file)
				if (os.access(path, os.X_OK) or lib_re.match(file)) and not os.path.islink(path):
					cmd = bb.data.getVar('OBJDUMP', d, 1) + " -p " + path + " 2>/dev/null"
					cmd = "PATH=\"%s\" %s" % (bb.data.getVar('PATH', d, 1), cmd)
					fd = os.popen(cmd)
					lines = fd.readlines()
					fd.close()
					for l in lines:
						m = re.match("\s+NEEDED\s+([^\s]*)", l)
						if m:
							needed[pkg].append(m.group(1))
						m = re.match("\s+SONAME\s+([^\s]*)", l)
						if m:
							this_soname = m.group(1)
							if not this_soname in sonames:
								# if library is private (only used by package) then do not build shlib for it
								if not private_libs or -1 == private_libs.find(this_soname):
									sonames.append(this_soname)
							if libdir_re.match(root):
								needs_ldconfig = True
							if snap_symlinks and (file != soname):
								renames.append((path, os.path.join(root, this_soname)))
		for (old, new) in renames:
			os.rename(old, new)
		shlibs_file = os.path.join(shlibs_dir, pkg + ".list")
		if os.path.exists(shlibs_file):
			os.remove(shlibs_file)
		shver_file = os.path.join(shlibs_dir, pkg + ".ver")
		if os.path.exists(shver_file):
			os.remove(shver_file)
		if len(sonames):
			fd = open(shlibs_file, 'w')
			for s in sonames:
				fd.write(s + '\n')
			fd.close()
			package_stagefile(shlibs_file, d)
			fd = open(shver_file, 'w')
			fd.write(ver + '\n')
			fd.close()
			package_stagefile(shver_file, d)
		if needs_ldconfig and use_ldconfig:
			bb.debug(1, 'adding ldconfig call to postinst for %s' % pkg)
			postinst = bb.data.getVar('pkg_postinst_%s' % pkg, d, 1) or bb.data.getVar('pkg_postinst', d, 1)
			if not postinst:
				postinst = '#!/bin/sh\n'
			postinst += bb.data.getVar('ldconfig_postinst_fragment', d, 1)
			bb.data.setVar('pkg_postinst_%s' % pkg, postinst, d)

	if pstageactive == "1":
		bb.utils.unlockfile(lf)

	shlib_provider = {}
	list_re = re.compile('^(.*)\.list$')
	for dir in [shlibs_dir]:
		if not os.path.exists(dir):
			continue
		for file in os.listdir(dir):
			m = list_re.match(file)
			if m:
				dep_pkg = m.group(1)
				fd = open(os.path.join(dir, file))
				lines = fd.readlines()
				fd.close()
				ver_file = os.path.join(dir, dep_pkg + '.ver')
				lib_ver = None
				if os.path.exists(ver_file):
					fd = open(ver_file)
					lib_ver = fd.readline().rstrip()
					fd.close()
				for l in lines:
					shlib_provider[l.rstrip()] = (dep_pkg, lib_ver)

	assumed_libs = bb.data.getVar('ASSUME_SHLIBS', d, 1)
	if assumed_libs:
	    for e in assumed_libs.split():
		l, dep_pkg = e.split(":")
		lib_ver = None
		dep_pkg = dep_pkg.rsplit("_", 1)
		if len(dep_pkg) == 2:
		    lib_ver = dep_pkg[1]
		dep_pkg = dep_pkg[0]
		shlib_provider[l] = (dep_pkg, lib_ver)

	dep_packages = []
	for pkg in packages.split():
		bb.debug(2, "calculating shlib requirements for %s" % pkg)

		deps = list()
		for n in needed[pkg]:
			if n in shlib_provider.keys():
				(dep_pkg, ver_needed) = shlib_provider[n]

				if dep_pkg == pkg:
					continue

				if ver_needed:
					dep = "%s (>= %s)" % (dep_pkg, ver_needed)
				else:
					dep = dep_pkg
				if not dep in deps:
					deps.append(dep)
				if not dep_pkg in dep_packages:
					dep_packages.append(dep_pkg)

			else:
				bb.note("Couldn't find shared library provider for %s" % n)

		deps_file = os.path.join(pkgd, pkg + ".shlibdeps")
		if os.path.exists(deps_file):
			os.remove(deps_file)
		if len(deps):
			fd = open(deps_file, 'w')
			for dep in deps:
				fd.write(dep + '\n')
			fd.close()
}

python package_do_pkgconfig () {
	import re, os

	packages = bb.data.getVar('PACKAGES', d, 1)

	workdir = bb.data.getVar('WORKDIR', d, 1)
	if not workdir:
		bb.error("WORKDIR not defined")
		return

	pkgd = bb.data.getVar('PKGD', d, 1)

	shlibs_dir = bb.data.getVar('SHLIBSDIR', d, 1)
	bb.mkdirhier(shlibs_dir)

	pc_re = re.compile('(.*)\.pc$')
	var_re = re.compile('(.*)=(.*)')
	field_re = re.compile('(.*): (.*)')

	pkgconfig_provided = {}
	pkgconfig_needed = {}
	for pkg in packages.split():
		pkgconfig_provided[pkg] = []
		pkgconfig_needed[pkg] = []
		top = os.path.join(pkgd, pkg)
		for root, dirs, files in os.walk(top):
			for file in files:
				m = pc_re.match(file)
				if m:
					pd = bb.data.init()
					name = m.group(1)
					pkgconfig_provided[pkg].append(name)
					path = os.path.join(root, file)
					if not os.access(path, os.R_OK):
						continue
					f = open(path, 'r')
					lines = f.readlines()
					f.close()
					for l in lines:
						m = var_re.match(l)
						if m:
							name = m.group(1)
							val = m.group(2)
							bb.data.setVar(name, bb.data.expand(val, pd), pd)
							continue
						m = field_re.match(l)
						if m:
							hdr = m.group(1)
							exp = bb.data.expand(m.group(2), pd)
							if hdr == 'Requires':
								pkgconfig_needed[pkg] += exp.replace(',', ' ').split()

	pstageactive = bb.data.getVar('PSTAGING_ACTIVE', d, True)
	if pstageactive == "1":
		lf = bb.utils.lockfile(bb.data.expand("${STAGING_DIR}/staging.lock", d))

	for pkg in packages.split():
		pkgs_file = os.path.join(shlibs_dir, pkg + ".pclist")
		if os.path.exists(pkgs_file):
			os.remove(pkgs_file)
		if pkgconfig_provided[pkg] != []:
			f = open(pkgs_file, 'w')
			for p in pkgconfig_provided[pkg]:
				f.write('%s\n' % p)
			f.close()
			package_stagefile(pkgs_file, d)

	for dir in [shlibs_dir]:
		if not os.path.exists(dir):
			continue
		for file in os.listdir(dir):
			m = re.match('^(.*)\.pclist$', file)
			if m:
				pkg = m.group(1)
				fd = open(os.path.join(dir, file))
				lines = fd.readlines()
				fd.close()
				pkgconfig_provided[pkg] = []
				for l in lines:
					pkgconfig_provided[pkg].append(l.rstrip())

	for pkg in packages.split():
		deps = []
		for n in pkgconfig_needed[pkg]:
			found = False
			for k in pkgconfig_provided.keys():
				if n in pkgconfig_provided[k]:
					if k != pkg and not (k in deps):
						deps.append(k)
					found = True
			if found == False:
				bb.note("couldn't find pkgconfig module '%s' in any package" % n)
		deps_file = os.path.join(pkgd, pkg + ".pcdeps")
		if os.path.exists(deps_file):
			os.remove(deps_file)
		if len(deps):
			fd = open(deps_file, 'w')
			for dep in deps:
				fd.write(dep + '\n')
			fd.close()
			package_stagefile(deps_file, d)

	if pstageactive == "1":
		bb.utils.unlockfile(lf)
}

python read_shlibdeps () {
	packages = bb.data.getVar('PACKAGES', d, 1).split()
	for pkg in packages:
		rdepends = bb.utils.explode_deps(bb.data.getVar('RDEPENDS_' + pkg, d, 0) or "")
		for extension in ".shlibdeps", ".pcdeps", ".clilibdeps":
			depsfile = bb.data.expand("${PKGD}/" + pkg + extension, d)
			if os.access(depsfile, os.R_OK):
				fd = file(depsfile)
				lines = fd.readlines()
				fd.close()
				for l in lines:
					rdepends.append(l.rstrip())
		bb.data.setVar('RDEPENDS_' + pkg, " " + " ".join(rdepends), d)
}

python package_depchains() {
	"""
	For a given set of prefix and postfix modifiers, make those packages
	RRECOMMENDS on the corresponding packages for its RDEPENDS.

	Example:  If package A depends upon package B, and A's .bb emits an
	A-dev package, this would make A-dev Recommends: B-dev.

	If only one of a given suffix is specified, it will take the RRECOMMENDS
	based on the RDEPENDS of *all* other packages. If more than one of a given
	suffix is specified, its will only use the RDEPENDS of the single parent
	package.
	"""

	packages  = bb.data.getVar('PACKAGES', d, 1)
	postfixes = (bb.data.getVar('DEPCHAIN_POST', d, 1) or '').split()
	prefixes  = (bb.data.getVar('DEPCHAIN_PRE', d, 1) or '').split()

	def pkg_adddeprrecs(pkg, base, suffix, getname, depends, d):

		#bb.note('depends for %s is %s' % (base, depends))
		rreclist = bb.utils.explode_deps(bb.data.getVar('RRECOMMENDS_' + pkg, d, 1) or bb.data.getVar('RRECOMMENDS', d, 1) or "")

		for depend in depends:
			if depend.find('-native') != -1 or depend.find('-cross') != -1 or depend.startswith('virtual/'):
				#bb.note("Skipping %s" % depend)
				continue
			if depend.endswith('-dev'):
				depend = depend.replace('-dev', '')
			if depend.endswith('-dbg'):
				depend = depend.replace('-dbg', '')
			pkgname = getname(depend, suffix)
			#bb.note("Adding %s for %s" % (pkgname, depend))
			if not pkgname in rreclist:
				rreclist.append(pkgname)

		#bb.note('setting: RRECOMMENDS_%s=%s' % (pkg, ' '.join(rreclist)))
		bb.data.setVar('RRECOMMENDS_%s' % pkg, ' '.join(rreclist), d)

	def pkg_addrrecs(pkg, base, suffix, getname, rdepends, d):

		#bb.note('rdepends for %s is %s' % (base, rdepends))
		rreclist = bb.utils.explode_deps(bb.data.getVar('RRECOMMENDS_' + pkg, d, 1) or bb.data.getVar('RRECOMMENDS', d, 1) or "")

		for depend in rdepends:
			if depend.endswith('-dev'):
				depend = depend.replace('-dev', '')
			if depend.endswith('-dbg'):
				depend = depend.replace('-dbg', '')
			pkgname = getname(depend, suffix)
			if not pkgname in rreclist:
				rreclist.append(pkgname)

		#bb.note('setting: RRECOMMENDS_%s=%s' % (pkg, ' '.join(rreclist)))
		bb.data.setVar('RRECOMMENDS_%s' % pkg, ' '.join(rreclist), d)

	def add_dep(list, dep):
		dep = dep.split(' (')[0].strip()
		if dep not in list:
			list.append(dep)

	depends = []
	for dep in bb.utils.explode_deps(bb.data.getVar('DEPENDS', d, 1) or ""):
		add_dep(depends, dep)

	rdepends = []
	for dep in bb.utils.explode_deps(bb.data.getVar('RDEPENDS', d, 1) or ""):
		add_dep(rdepends, dep)

	for pkg in packages.split():
		for dep in bb.utils.explode_deps(bb.data.getVar('RDEPENDS_' + pkg, d, 1) or ""):
			add_dep(rdepends, dep)

	#bb.note('rdepends is %s' % rdepends)

	def post_getname(name, suffix):
		return '%s%s' % (name, suffix)
	def pre_getname(name, suffix):
		return '%s%s' % (suffix, name)

	pkgs = {}
	for pkg in packages.split():
		for postfix in postfixes:
			if pkg.endswith(postfix):
				if not postfix in pkgs:
					pkgs[postfix] = {}
				pkgs[postfix][pkg] = (pkg[:-len(postfix)], post_getname)

		for prefix in prefixes:
			if pkg.startswith(prefix):
				if not prefix in pkgs:
					pkgs[prefix] = {}
				pkgs[prefix][pkg] = (pkg[:-len(prefix)], pre_getname)

	for suffix in pkgs:
		for pkg in pkgs[suffix]:
			(base, func) = pkgs[suffix][pkg]
			if suffix == "-dev" and not pkg.startswith("kernel-module-"):
				pkg_adddeprrecs(pkg, base, suffix, func, depends, d)
			if len(pkgs[suffix]) == 1:
				pkg_addrrecs(pkg, base, suffix, func, rdepends, d)
			else:
				rdeps = []
				for dep in bb.utils.explode_deps(bb.data.getVar('RDEPENDS_' + base, d, 1) or bb.data.getVar('RDEPENDS', d, 1) or ""):
					add_dep(rdeps, dep)
				pkg_addrrecs(pkg, base, suffix, func, rdeps, d)
}


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
