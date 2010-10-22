BB_DEFAULT_TASK ?= "build"

inherit arch
inherit utils
inherit stage
inherit patch
inherit package
inherit mirrors

# FIXME: inherit in specialized classes, so that fx. image does not have
# to have do_fetch
inherit fetch

EXPORT_FUNCTIONS do_clean do_fetch do_unpack do_configure do_compile do_install
addtask listtasks
addtask clean
addtask rebuild after do_${BB_DEFAULT_TASK}
addtask checkuri
addtask checkuriall after do_checkuri
addtask buildall after do_build
addtask configure after do_unpack do_patch
addtask compile after do_configure
addtask install after do_compile
addtask install_fixup after do_install before do_package_install
addtask build after do_install

do_build = ""
do_build[func] = "1"


# Default recipe type is machine, so other recipe type classes must
# override this, and any other recipe type defaults as needed
RECIPE_TYPE = "machine"
RE = ""

DEFAULT_DEPENDS = "${HOST_ARCH}/toolchain ${HOST_ARCH}/sysroot-dev"
DEPENDS_prepend = "${DEFAULT_DEPENDS} "


FILESPATH = "${@base_set_filespath([ "${FILE_DIRNAME}/${PF}", "${FILE_DIRNAME}/${P}", "${FILE_DIRNAME}/${PN}", "${FILE_DIRNAME}/${BP}", "${FILE_DIRNAME}/${BPN}", "${FILE_DIRNAME}/files", "${FILE_DIRNAME}" ], d)}"

die() {
	oefatal "$*"
}

oenote() {
	echo "NOTE:" "$*"
}

oewarn() {
	echo "WARNING:" "$*"
}

oefatal() {
	echo "FATAL:" "$*"
	exit 1
}

oedebug() {
	test $# -ge 2 || {
		echo "Usage: oedebug level \"message\""
		exit 1
	}

	test ${OEDEBUG:-0} -ge $1 && {
		shift
		echo "DEBUG:" $*
	}
}

oe_runmake() {
	if [ x"$MAKE" = x ]; then MAKE=make; fi
	oenote ${MAKE} ${EXTRA_OEMAKE} "$@"
	${MAKE} ${EXTRA_OEMAKE} "$@" || die "oe_runmake failed"
}


oe_machinstall() {
	# Purpose: Install machine dependent files, if available
	#          If not available, check if there is a default
	#          If no default, just touch the destination
	# Example:
	#                $1  $2   $3         $4
	# oe_machinstall -m 0644 fstab ${D}/etc/fstab
	#
	# TODO: Check argument number?
	#
	filename=`basename $3`
	dirname=`dirname $3`

	for o in `echo ${OVERRIDES} | tr ':' ' '`; do
		if [ -e $dirname/$o/$filename ]; then
			oenote $dirname/$o/$filename present, installing to $4
			install $1 $2 $dirname/$o/$filename $4
			return
		fi
	done
#	oenote overrides specific file NOT present, trying default=$3...
	if [ -e $3 ]; then
		oenote $3 present, installing to $4
		install $1 $2 $3 $4
	else
		oenote $3 NOT present, touching empty $4
		touch $4
	fi
}

do_listtasks[nostamp] = "1"
python do_listtasks() {
	import sys
	# emit variables and shell functions
	#bb.data.emit_env(sys.__stdout__, d)
	# emit the metadata which isnt valid shell
	for e in d.keys():
		if bb.data.getVarFlag(e, 'task', d):
			sys.__stdout__.write("%s\n" % e)
}

do_clean[dirs] = "${TOPDIR}"
do_clean[nostamp] = "1"
python base_do_clean() {
	"""clear the build and temp directories"""
	dir = bb.data.expand("${WORKDIR}", d)
	if dir == '//': raise bb.build.FuncFailed("wrong DATADIR")
	bb.note("removing " + dir)
	os.system('rm -rf ' + dir)

	dir = "%s.*" % bb.data.expand(bb.data.getVar('STAMP', d), d)
	bb.note("removing " + dir)
	os.system('rm -f '+ dir)
}

do_rebuild[dirs] = "${TOPDIR}"
do_rebuild[nostamp] = "1"
python base_do_rebuild() {
	"""rebuild a package"""
}


do_checkuri[nostamp] = "1"
python do_checkuri() {
	import sys

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

	src_uri = bb.data.getVar('SRC_URI', localdata, 1)

	try:
		bb.fetch.init(src_uri.split(),d)
	except bb.fetch.NoMethodError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("No method: %s" % value)

	try:
		bb.fetch.checkstatus(localdata)
	except bb.fetch.MissingParameterError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("Missing parameters: %s" % value)
	except bb.fetch.FetchError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("Fetch failed: %s" % value)
	except bb.fetch.MD5SumError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("MD5  failed: %s" % value)
	except:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("Unknown fetch Error: %s" % value)
}

do_checkuriall[recrdeptask] = "do_checkuri"
do_checkuriall[nostamp] = "1"
base_do_checkuriall() {
	:
}

do_buildall[recrdeptask] = "do_build"
base_do_buildall() {
	:
}

def subprocess_setup():
	import signal
	# Python installs a SIGPIPE handler by default. This is usually not what
	# non-Python subprocesses expect.
	# SIGPIPE errors are known issues with gzip/bash
	signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def oe_unpack_file(file, data, url = None):
	import subprocess
	if not url:
		url = "file://%s" % file
	dots = file.split(".")
	if dots[-1] in ['gz', 'bz2', 'Z']:
		efile = os.path.join(bb.data.getVar('WORKDIR', data, 1),os.path.basename('.'.join(dots[0:-1])))
	else:
		efile = file
	cmd = None
	if file.endswith('.tar'):
		cmd = 'tar x --no-same-owner -f %s' % file
	elif file.endswith('.tgz') or file.endswith('.tar.gz') or file.endswith('.tar.Z'):
		cmd = 'tar xz --no-same-owner -f %s' % file
	elif file.endswith('.tbz') or file.endswith('.tbz2') or file.endswith('.tar.bz2'):
		cmd = 'bzip2 -dc %s | tar x --no-same-owner -f -' % file
	elif file.endswith('.gz') or file.endswith('.Z') or file.endswith('.z'):
		cmd = 'gzip -dc %s > %s' % (file, efile)
	elif file.endswith('.bz2'):
		cmd = 'bzip2 -dc %s > %s' % (file, efile)
	elif file.endswith('.zip') or file.endswith('.jar'):
		cmd = 'unzip -q -o'
		(type, host, path, user, pswd, parm) = bb.decodeurl(url)
		if 'dos' in parm:
			cmd = '%s -a' % cmd
		cmd = "%s '%s'" % (cmd, file)
	elif os.path.isdir(file):
		filesdir = os.path.realpath(bb.data.getVar("FILESDIR", data, 1))
		destdir = "."
		if file[0:len(filesdir)] == filesdir:
			destdir = file[len(filesdir):file.rfind('/')]
			destdir = destdir.strip('/')
			if len(destdir) < 1:
				destdir = "."
			elif not os.access("%s/%s" % (os.getcwd(), destdir), os.F_OK):
				os.makedirs("%s/%s" % (os.getcwd(), destdir))
		cmd = 'cp -pPR %s %s/%s/' % (file, os.getcwd(), destdir)
	else:
		(type, host, path, user, pswd, parm) = bb.decodeurl(url)
		if not 'patch' in parm:
			# The "destdir" handling was specifically done for FILESPATH
			# items.  So, only do so for file:// entries.
			if type == "file":
				destdir = bb.decodeurl(url)[1] or "."
			else:
				destdir = "."
			bb.mkdirhier("%s/%s" % (os.getcwd(), destdir))
			cmd = 'cp %s %s/%s/' % (file, os.getcwd(), destdir)

	if not cmd:
		return True

	dest = os.path.join(os.getcwd(), os.path.basename(file))
	if os.path.exists(dest):
		if os.path.samefile(file, dest):
			return True

	# Change to subdir before executing command
	save_cwd = os.getcwd();
	parm = bb.decodeurl(url)[5]
	if 'subdir' in parm:
		newdir = ("%s/%s" % (os.getcwd(), parm['subdir']))
		bb.mkdirhier(newdir)
		os.chdir(newdir)

	cmd = "PATH=\"%s\" %s" % (bb.data.getVar('PATH', data, 1), cmd)
	bb.note("Unpacking %s to %s/" % (file, os.getcwd()))
	ret = subprocess.call(cmd, preexec_fn=subprocess_setup, shell=True)

	os.chdir(save_cwd)

	return ret == 0


addhandler base_eventhandler
python base_eventhandler() {
	from bb import note, error, data
	from bb.event import Handled, NotHandled, getName

	messages = {}
	messages["Completed"] = "completed"
	messages["Succeeded"] = "completed"
	messages["Started"] = "started"
	messages["Failed"] = "failed"

	name = getName(e)
	msg = ""
	if name.startswith("Pkg"):
		msg += "package %s: " % data.getVar("P", e.data, 1)
		msg += messages.get(name[3:]) or name[3:]
	elif name.startswith("Task"):
		msg += "package %s: task %s: " % (data.getVar("PF", e.data, 1), e.task)
		msg += messages.get(name[4:]) or name[4:]
	elif name.startswith("Build"):
		msg += "build %s: " % e.name
		msg += messages.get(name[5:]) or name[5:]
	elif name == "UnsatisfiedDep":
		msg += "package %s: dependency %s %s" % (e.pkg, e.dep, name[:-3].lower())

	# Only need to output when using 1.8 or lower, the UI code handles it
	# otherwise
	if (int(bb.__version__.split(".")[0]) <= 1 and int(bb.__version__.split(".")[1]) <= 8):
		if msg:
			note(msg)

	if name.startswith("BuildStarted"):
		bb.data.setVar( 'BB_VERSION', bb.__version__, e.data )
		statusvars = ['BB_VERSION', 'MACHINE', 'MACHINE_CPU', 'MACHINE_OS', 'SDK_CPU', 'SDK_OS', 'DISTRO', 'DISTRO_VERSION']
		statuslines = ["%-17s = \"%s\"" % (i, bb.data.getVar(i, e.data, 1) or '') for i in statusvars]
		statusmsg = "\nOE Build Configuration:\n%s\n" % '\n'.join(statuslines)
		print statusmsg

		needed_vars = [ "MACHINE_CPU", "MACHINE_OS" ]
		pesteruser = []
		for v in needed_vars:
			val = bb.data.getVar(v, e.data, 1)
			if not val or val == 'INVALID':
				pesteruser.append(v)
		if pesteruser:
			bb.fatal('The following variable(s) were not set: %s\nPlease set them directly, or choose a MACHINE or DISTRO that sets them.' % ', '.join(pesteruser))

	#
	# Handle removing stamps for 'rebuild' task
	#
	if name.startswith("StampUpdate"):
		for (fn, task) in e.targets:
			#print "%s %s" % (task, fn)
			if task == "do_rebuild":
				dir = "%s.*" % e.stampPrefix[fn]
				bb.note("Removing stamps: " + dir)
				os.system('rm -f '+ dir)
				os.system('touch ' + e.stampPrefix[fn] + '.needclean')

	if not data in e.__dict__:
		return NotHandled

	log = data.getVar("EVENTLOG", e.data, 1)
	if log:
		logfile = file(log, "a")
		logfile.write("%s\n" % msg)
		logfile.close()

	return NotHandled
}

do_configure[dirs] = "${S} ${B}"
#do_configure[deptask] = "do_populate_sysroot"
base_do_configure() {
	:
}

do_compile[dirs] = "${S} ${B}"
base_do_compile() {
	if [ -e Makefile -o -e makefile ]; then
		oe_runmake || die "make failed"
	else
		oenote "nothing to compile"
	fi
}




do_install[dirs] = "${D} ${S} ${B}"
# Remove and re-create ${D} so that is it guaranteed to be empty
do_install[cleandirs] = "${D}"

base_do_install() {
	:
}

INSTALL_FIXUP_FUNCS = "\
install_strip \
#install_refactor \
install_fixup"

python do_install_fixup () {
	for f in (bb.data.getVar('INSTALL_FIXUP_FUNCS', d, 1) or '').split():
		bb.build.exec_func(f, d)
}
do_install_fixup[dirs] = "${D}"

python install_strip () {
    import stat
    def isexec(path):
	try:
	    s = os.stat(path)
	except (os.error, AttributeError):
	    return 0
	return (s[stat.ST_MODE] & stat.S_IEXEC)

    if (bb.data.getVar('INHIBIT_PACKAGE_STRIP', d, True) != '1'):
	for root, dirs, files in os.walk(os.getcwd()):
	    for f in files:
	       file = os.path.join(root, f)
	       if not os.path.islink(file) and not os.path.isdir(file) and isexec(file):
		   runstrip(file, d)
}
install_strip[dirs] = "${D}"

def runstrip(file, d):
    # Function to strip a single file, called from populate_packages below
    # A working 'file' (one which works on the target architecture)
    # is necessary for this stuff to work, hence the addition to do_package[depends]

    import commands, stat

    pathprefix = "export PATH=%s; " % bb.data.getVar('PATH', d, True)

    ret, result = commands.getstatusoutput("%sfile '%s'" % (pathprefix, file))

    if ret:
	bb.fatal("runstrip() 'file %s' failed" % file)

    if "not stripped" not in result:
	bb.debug(1, "runstrip() skip %s" % file)
	return

    target_elf = bb.data.getVar('TARGET_ELF', d, True)
    if not target_elf:
	bb.debug(1, "TARGET_ELF not defined, you might want to fix this...")
	return

    if target_elf not in result:
	bb.debug(1, "runstrip() target_elf(%s) not in %s" %(target_elf,result))
	return

    # If the file is in a .debug directory it was already stripped,
    # don't do it again...
    if os.path.dirname(file).endswith(".debug"):
	bb.note("Already ran strip")
	return

    strip = bb.data.getVar("STRIP", d, True)
    if not len(strip) >0:
	bb.note("runstrip() STRIP var empty")
	return

    objcopy = bb.data.getVar("OBJCOPY", d, True)
    if not len(objcopy) >0:
	bb.note("runstrip() OBJCOPY var empty")
	return

    newmode = None
    if not os.access(file, os.W_OK):
	origmode = os.stat(file)[stat.ST_MODE]
	newmode = origmode | stat.S_IWRITE
	os.chmod(file, newmode)

    extraflags = ""
    if ".so" in file and "shared" in result:
	extraflags = "--remove-section=.comment --remove-section=.note --strip-unneeded"
    elif "shared" in result or "executable" in result:
	extraflags = "--remove-section=.comment --remove-section=.note"

    bb.mkdirhier(os.path.join(os.path.dirname(file), ".debug"))
    debugfile=os.path.join(os.path.dirname(file), ".debug", os.path.basename(file))

    stripcmd = "'%s' %s '%s'"                       % (strip, extraflags, file)
    objcpcmd = "'%s' --only-keep-debug '%s' '%s'"   % (objcopy, file, debugfile)
    objlncmd = "'%s' --add-gnu-debuglink='%s' '%s'" % (objcopy, debugfile, file)

    bb.debug(1, "runstrip() %s" % objcpcmd)
    bb.debug(1, "runstrip() %s" % stripcmd)
    bb.debug(1, "runstrip() %s" % objlncmd)

    ret, result = commands.getstatusoutput("%s%s" % (pathprefix, objcpcmd))
    if ret:
	bb.note("runstrip() '%s' %s" % (objcpcmd,result))

    ret, result = commands.getstatusoutput("%s%s" % (pathprefix, stripcmd))
    if ret:
	bb.note("runstrip() '%s' %s" % (stripcmd,result))

    ret, result = commands.getstatusoutput("%s%s" % (pathprefix, objlncmd))
    if ret:
	bb.note("runstrip() '%s' %s" % (objlncmd,result))

    if newmode:
	os.chmod(file, origmode)



# Make sure MACHINE isn't exported
# (breaks binutils at least)
MACHINE[unexport] = "1"

# Make sure TARGET_ARCH isn't exported
# (breaks Makefiles using implicit rules, e.g. quilt, as GNU make has this
# in them, undocumented)
TARGET_ARCH[unexport] = "1"

# Make sure DISTRO isn't exported
# (breaks sysvinit at least)
DISTRO[unexport] = "1"


def srcuri_machine_override(d, srcuri):
    import bb
    import os

    paths = []
    # FIXME: this should use FILESPATHPKG
    for p in [ "${PF}", "${P}", "${PN}", "files", "" ]:
	path = bb.data.expand(os.path.join("${FILE_DIRNAME}", p, "${MACHINE}"), d)
	if os.path.isdir(path):
	    paths.append(path)
    if len(paths) != 0:
	for s in srcuri.split():
	    if not s.startswith("file://"):
		continue
	    local = bb.data.expand(bb.fetch.localpath(s, d), d)
	    for mp in paths:
		if local.startswith(mp):
		    return True
    return False


FIXUP_PACKAGE_ARCH = base_fixup_package_arch
def base_fixup_package_arch(d):
    arch_prefix = bb.data.getVar('RECIPE_TYPE', d, True) + '/'
    arch = bb.data.getVar('RECIPE_ARCH', d, True).partition(arch_prefix)
    # take part after / of RECIPE_ARCH if it begins with $RECIPE_TYPE/
    if not arch[0] and arch[1]:
	arch = arch[2]
    else:
	arch = '${TARGET_ARCH}'
    for pkg in bb.data.getVar('PACKAGES', d, True).split():
	if not bb.data.getVar('PACKAGE_ARCH_'+pkg, d, False):
	    pkg_arch = 'sysroot/'+arch
	    bb.data.setVar('PACKAGE_ARCH_'+pkg, pkg_arch, d)


FIXUP_PROVIDES = base_fixup_provides
def base_fixup_provides(d):
    for pkg in bb.data.getVar('PACKAGES', d, True).split():
    	provides = (bb.data.getVar('PROVIDES_'+pkg, d, True) or '').split()
	if not pkg in provides:
	    bb.data.setVar('PROVIDES_'+pkg, ' '.join([pkg] + provides), d)
    	rprovides = (bb.data.getVar('RPROVIDES_'+pkg, d, True) or '').split()
	if not pkg in rprovides:
	    bb.data.setVar('RPROVIDES_'+pkg, ' '.join([pkg] + rprovides), d)


def base_after_parse(d):
    import bb

    source_mirror_fetch = bb.data.getVar('SOURCE_MIRROR_FETCH', d, 0)

    if not source_mirror_fetch:
	need_host = bb.data.getVar('COMPATIBLE_HOST', d, 1)
	if need_host:
	    import re
	    this_host = bb.data.getVar('HOST_SYS', d, 1)
	    if not re.match(need_host, this_host):
		raise bb.parse.SkipPackage("incompatible with host %s" % this_host)

	need_machine = bb.data.getVar('COMPATIBLE_MACHINE', d, 1)
	if need_machine:
	    import re
	    this_machine = bb.data.getVar('MACHINE', d, 1)
	    if this_machine and not re.match(need_machine, this_machine):
		raise bb.parse.SkipPackage("incompatible with machine %s" % this_machine)

    pn = bb.data.getVar('PN', d, 1)

    use_nls = bb.data.getVar('USE_NLS_%s' % pn, d, 1)
    if use_nls != None:
	bb.data.setVar('USE_NLS', use_nls, d)

    fetcher_depends = ""

    # Git packages should DEPEND on git-native
    srcuri = bb.data.getVar('SRC_URI', d, 1)
    if "git://" in srcuri:
	fetcher_depends += " git-native "

    # Mercurial packages should DEPEND on mercurial-native
    elif "hg://" in srcuri:
	fetcher_depends += " mercurial-native "

    # OSC packages should DEPEND on osc-native
    elif "osc://" in srcuri:
	fetcher_depends += " osc-native "

    # bb.utils.sha256_file() will fail if hashlib isn't present, so we fallback
    # on shasum-native.  We need to ensure that it is staged before we fetch.
    if bb.data.getVar('PN', d, True) != "shasum-native":
	try:
	    import hashlib
	except ImportError:
	    fetcher_depends += " shasum-native"

    bb.data.setVar('FETCHER_DEPENDS', fetcher_depends[1:], d)

    # Special handling of BBCLASSEXTEND recipes
    # FIXME: let's rename BBCLASSEXTEND to RECIPE_EXTEND as it makes much
    # more sense
    recipe_type = bb.data.getVar('RECIPE_TYPE', d, True)
    if recipe_type in (bb.data.getVar('BBCLASSEXTEND', d, True) or "").split():
	# Set ${RE} for use in fx. DEPENDS and RDEPENDS
	bb.data.setVar('RE', '-' + recipe_type, d)
	# Add recipe-${RECIPE_TYPE} to OVERRIDES
	bb.data.setVar('OVERRIDES', bb.data.getVar('OVERRIDES', d, False) + ':recipe-'+recipe_type, d)

    # FIXME: move to insane.bbclass
    provides = bb.data.getVar('PROVIDES', d, True)
    if provides:
	bb.note("Ignoring PROVIDES as it does not make sense with OE-core (PROVIDES='%s')"%provides)

    # FIXME: move to insane.bbclass
    rprovides = bb.data.getVar('RPROVIDES', d, True)
    if rprovides:
	bb.note("Ignoring RPROVIDES as it does not make sense with OE-core (RPROVIDES='%s')"%rprovides)

    # Fixup package PACKAGE_ARCH (recipe type dependant)
    fixup_package_arch = bb.data.getVar('FIXUP_PACKAGE_ARCH', d, False)
    if fixup_package_arch is not '':
	eval(fixup_package_arch)(d)

    # Fixup package PROVIDES and RPROVIDES (recipe type dependant)
    fixup_provides = bb.data.getVar('FIXUP_PROVIDES', d, False)
    if fixup_provides is not '':
	eval(fixup_provides)(d)

    # RECIPE_ARCH override detection
    recipe_arch = bb.data.getVar('RECIPE_ARCH', d, 1)
    recipe_arch_mach = bb.data.getVar('RECIPE_ARCH_MACHINE', d, 1)

    # Scan SRC_URI for urls with machine overrides unless the package
    # sets SRC_URI_OVERRIDES_RECIPE_ARCH=0
    override = bb.data.getVar('SRC_URI_OVERRIDES_RECIPE_ARCH', d, 1)

    if (recipe_arch != recipe_arch_mach and override != '0' and
	srcuri_machine_override(d, srcuri)):
	bb.debug("%s SRC_URI overrides RECIPE_ARCH from %s to %s"%
		 (pn, recipe_arch, recipe_arch_mach))
	bb.data.setVar('RECIPE_ARCH', "${RECIPE_ARCH_MACHINE}", d)
	recipe_arch = recipe_arch_mach

    # Detect manual machine "override" in PACKAGE_ARCH_* variables
    # FIXME: if PACKAGES has overrides, this will break as
    # overrides has not been applied at this point in time!
    packages = bb.data.getVar('PACKAGES', d, True)
    for pkg in packages:
	package_arch = bb.data.getVar("PACKAGE_ARCH_%s" % pkg, d, True)
	if package_arch and package_arch == recipe_arch_mach:
	    if recipe_arch != recipe_arch_mach:
		bb.debug("PACKAGE_ARCH_%s overrides RECIPE_ARCH from %s to %s"%
			 (pkg, recipe_arch, recipe_arch_mach))
		bb.data.setVar('RECIPE_ARCH', "${RECIPE_ARCH_MACHINE}", d)
	    break

#
# RECIPE_OPTIONS are to be defined in recipes, and should be a
# space-separated list of upper-case options, preferably prefixed with
# the recipe name (in upper-case).
#
# Distro configuration files can then define these as needed, and set
# them to the desired values, enabling distro customization of recipes
# without the need to include anything about the distros in the
# meta-data repository holding the repository.
#
def base_apply_recipe_options(d):
	import bb
	recipe_options = (bb.data.getVar('RECIPE_OPTIONS', d, 1) or "")
	if not recipe_options:
		return
	recipe_arch = bb.data.getVar('RECIPE_ARCH', d, 1)
	recipe_arch_mach = bb.data.getVar('RECIPE_ARCH_MACHINE', d, 1)
	overrides = (bb.data.getVar('OVERRIDES', d, 1) or "")
	overrides_changed = False
	for option in recipe_options.split():
		recipe_val = bb.data.getVar('RECIPE_CONFIG_'+option, d, 1)
		machine_val = bb.data.getVar('MACHINE_CONFIG_'+option, d, 1)
		distro_val = bb.data.getVar('DISTRO_CONFIG_'+option, d, 1)
		default_val = bb.data.getVar('DEFAULT_CONFIG_'+option, d, 1)
		if recipe_val:
			val = recipe_val
		elif machine_val:
			if recipe_arch != recipe_arch_mach:
				bb.data.setVar('RECIPE_ARCH', '${RECIPE_ARCH_MACHINE}', d)
			val = machine_val
		elif distro_val:
			val = distro_val
		else:
			val = default_val
		if val and val != "0":
			bb.data.setVar('RECIPE_OPTION_'+option, val, d)
			overrides += ':RECIPE_OPTION_'+option
			overrides_changed = True
	if overrides_changed:
		bb.data.setVar('OVERRIDES', overrides, d)
	return

python () {
    base_after_parse(d)
    base_apply_recipe_options(d)
}

def check_app_exists(app, d):
	from bb import which, data

	app = data.expand(app, d)
	path = data.getVar('PATH', d, 1)
	return len(which(path, app)) != 0
