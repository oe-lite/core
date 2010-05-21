BB_DEFAULT_TASK ?= "build"

RECIPE_TYPE = "machine"
RE = ""

inherit base_arch

# like os.path.join but doesn't treat absolute RHS specially
def base_path_join(a, *p):
    path = a
    for b in p:
        if path == '' or path.endswith('/'):
            path +=  b
        else:
            path += '/' + b
    return path

DEFAULT_DEPENDS = "${HOST_ARCH}/toolchain ${HOST_ARCH}/sysroot-dev"
DEPENDS_prepend = "${DEFAULT_DEPENDS} "

def base_read_file(filename):
	try:
		f = file( filename, "r" )
	except IOError, reason:
		return "" # WARNING: can't raise an error now because of the new RDEPENDS handling. This is a bit ugly. :M:
	else:
		return f.read().strip()
	return None

def base_conditional(variable, checkvalue, truevalue, falsevalue, d):
	if bb.data.getVar(variable,d,1) == checkvalue:
		return truevalue
	else:
		return falsevalue

def base_less_or_equal(variable, checkvalue, truevalue, falsevalue, d):
	if float(bb.data.getVar(variable,d,1)) <= float(checkvalue):
		return truevalue
	else:
		return falsevalue

def base_version_less_or_equal(variable, checkvalue, truevalue, falsevalue, d):
    result = bb.vercmp(bb.data.getVar(variable,d,True), checkvalue)
    if result <= 0:
        return truevalue
    else:
        return falsevalue

def base_contains(variable, checkvalues, truevalue, falsevalue, d):
	matches = 0
	if type(checkvalues).__name__ == "str":
		checkvalues = [checkvalues]
	for value in checkvalues:
		if bb.data.getVar(variable,d,1).find(value) != -1:	
			matches = matches + 1
	if matches == len(checkvalues):
		return truevalue		
	return falsevalue

def base_both_contain(variable1, variable2, checkvalue, d):
       if bb.data.getVar(variable1,d,1).find(checkvalue) != -1 and bb.data.getVar(variable2,d,1).find(checkvalue) != -1:
               return checkvalue
       else:
               return ""


FETCHER_DEPENDS = ""
DEPENDS_prepend += "${FETCHER_DEPENDS}"

def base_prune_suffix(var, suffixes, d):
    # See if var ends with any of the suffixes listed and 
    # remove it if found
    for suffix in suffixes:
        if var.endswith(suffix):
            return var.replace(suffix, "")
    return var

def base_set_filespath(path, d):
	filespath = []
	# The ":" ensures we have an 'empty' override
	overrides = (bb.data.getVar("OVERRIDES", d, 1) or "") + ":"
	for p in path:
		for o in overrides.split(":"):
			filespath.append(os.path.join(p, o))
	return ":".join(filespath)

FILESPATH = "${@base_set_filespath([ "${FILE_DIRNAME}/${PF}", "${FILE_DIRNAME}/${P}", "${FILE_DIRNAME}/${PN}", "${FILE_DIRNAME}/${BP}", "${FILE_DIRNAME}/${BPN}", "${FILE_DIRNAME}/files", "${FILE_DIRNAME}" ], d)}"

def oe_filter(f, str, d):
	from re import match
	return " ".join(filter(lambda x: match(f, x, 0), str.split()))

def oe_filter_out(f, str, d):
	from re import match
	return " ".join(filter(lambda x: not match(f, x, 0), str.split()))

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

oe_soinstall() {
	# Purpose: Install shared library file and
	#          create the necessary links
	# Example:
	#
	# oe_
	#
	#oenote installing shared library $1 to $2
	#
	libname=`basename $1`
	install -m 755 $1 $2/$libname
	sonamelink=`${HOST_PREFIX}readelf -d $1 |grep 'Library soname:' |sed -e 's/.*\[\(.*\)\].*/\1/'`
	solink=`echo $libname | sed -e 's/\.so\..*/.so/'`
	ln -sf $libname $2/$sonamelink
	ln -sf $libname $2/$solink
}

oe_libinstall() {
	# Purpose: Install a library, in all its forms
	# Example
	#
	# oe_libinstall libltdl ${STAGING_LIBDIR}/
	# oe_libinstall -C src/libblah libblah ${D}/${libdir}/
	dir=""
	libtool=""
	silent=""
	require_static=""
	require_shared=""
	staging_install=""
	while [ "$#" -gt 0 ]; do
		case "$1" in
		-C)
			shift
			dir="$1"
			;;
		-s)
			silent=1
			;;
		-a)
			require_static=1
			;;
		-so)
			require_shared=1
			;;
		-*)
			oefatal "oe_libinstall: unknown option: $1"
			;;
		*)
			break;
			;;
		esac
		shift
	done

	libname="$1"
	shift
	destpath="$1"
	if [ -z "$destpath" ]; then
		oefatal "oe_libinstall: no destination path specified"
	fi
	if echo "$destpath/" | egrep '^${STAGING_LIBDIR}/' >/dev/null
	then
		staging_install=1
	fi

	__runcmd () {
		if [ -z "$silent" ]; then
			echo >&2 "oe_libinstall: $*"
		fi
		$*
	}

	if [ -z "$dir" ]; then
		dir=`pwd`
	fi

	dotlai=$libname.lai

	# Sanity check that the libname.lai is unique
	number_of_files=`(cd $dir; find . -name "$dotlai") | wc -l`
	if [ $number_of_files -gt 1 ]; then
		oefatal "oe_libinstall: $dotlai is not unique in $dir"
	fi


	dir=$dir`(cd $dir;find . -name "$dotlai") | sed "s/^\.//;s/\/$dotlai\$//;q"`
	olddir=`pwd`
	__runcmd cd $dir

	lafile=$libname.la

	# If such file doesn't exist, try to cut version suffix
	if [ ! -f "$lafile" ]; then
		libname1=`echo "$libname" | sed 's/-[0-9.]*$//'`
		lafile1=$libname.la
		if [ -f "$lafile1" ]; then
			libname=$libname1
			lafile=$lafile1
		fi
	fi

	if [ -f "$lafile" ]; then
		# libtool archive
		eval `cat $lafile|grep "^library_names="`
		libtool=1
	else
		library_names="$libname.so* $libname.dll.a"
	fi

	__runcmd install -d $destpath/
	dota=$libname.a
	if [ -f "$dota" -o -n "$require_static" ]; then
		rm -f $destpath/$dota
		__runcmd install -m 0644 $dota $destpath/
	fi
	if [ -f "$dotlai" -a -n "$libtool" ]; then
		if test -n "$staging_install"
		then
			# stop libtool using the final directory name for libraries
			# in staging:
			__runcmd rm -f $destpath/$libname.la
			__runcmd sed -e 's/^installed=yes$/installed=no/' \
				     -e '/^dependency_libs=/s,${WORKDIR}[[:alnum:]/\._+-]*/\([[:alnum:]\._+-]*\),${STAGING_LIBDIR}/\1,g' \
				     -e "/^dependency_libs=/s,\([[:space:]']\)${libdir},\1${STAGING_LIBDIR},g" \
				     $dotlai >$destpath/$libname.la
		else
			rm -f $destpath/$libname.la
			__runcmd install -m 0644 $dotlai $destpath/$libname.la
		fi
	fi

	for name in $library_names; do
		files=`eval echo $name`
		for f in $files; do
			if [ ! -e "$f" ]; then
				if [ -n "$libtool" ]; then
					oefatal "oe_libinstall: $dir/$f not found."
				fi
			elif [ -L "$f" ]; then
				__runcmd cp -P "$f" $destpath/
			elif [ ! -L "$f" ]; then
				libfile="$f"
				rm -f $destpath/$libfile
				__runcmd install -m 0755 $libfile $destpath/
			fi
		done
	done

	if [ -z "$libfile" ]; then
		if  [ -n "$require_shared" ]; then
			oefatal "oe_libinstall: unable to locate shared library"
		fi
	elif [ -z "$libtool" ]; then
		# special case hack for non-libtool .so.#.#.# links
		baselibfile=`basename "$libfile"`
		if (echo $baselibfile | grep -qE '^lib.*\.so\.[0-9.]*$'); then
			sonamelink=`${HOST_PREFIX}readelf -d $libfile |grep 'Library soname:' |sed -e 's/.*\[\(.*\)\].*/\1/'`
			solink=`echo $baselibfile | sed -e 's/\.so\..*/.so/'`
			if [ -n "$sonamelink" -a x"$baselibfile" != x"$sonamelink" ]; then
				__runcmd ln -sf $baselibfile $destpath/$sonamelink
			fi
			__runcmd ln -sf $baselibfile $destpath/$solink
		fi
	fi

	__runcmd cd "$olddir"
}

inherit package

# FIXME: move all package_stage stuff to package.bbclass

def package_stagefile(file, d):

    if bb.data.getVar('PSTAGING_ACTIVE', d, True) == "1":
        destfile = file.replace(bb.data.getVar("TMPDIR", d, 1), bb.data.getVar("PSTAGE_TMPDIR_STAGE", d, 1))
        bb.mkdirhier(os.path.dirname(destfile))
        #print "%s to %s" % (file, destfile)
        bb.copyfile(file, destfile)

package_stagefile_shell() {
	if [ "$PSTAGING_ACTIVE" = "1" ]; then
		srcfile=$1
		destfile=`echo $srcfile | sed s#${TMPDIR}#${PSTAGE_TMPDIR_STAGE}#`
		destdir=`dirname $destfile`
		mkdir -p $destdir
		cp -dp $srcfile $destfile
	fi
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

addtask listtasks
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

addtask clean
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

addtask rebuild after do_${BB_DEFAULT_TASK}
do_rebuild[dirs] = "${TOPDIR}"
do_rebuild[nostamp] = "1"
python base_do_rebuild() {
	"""rebuild a package"""
}

SCENEFUNCS += "base_scenefunction"


def set_stage_add(dep, d):
    bb.debug(2, 'adding build dependency %s to stage'%dep)

    # FIXME: we should find a way to avoid building recipes needed for
    # stage packages which is present (pre-baked) in deploy/stage dir.
    # perhaps we can dynamically add stage_packages to ASSUME_PROVIDED
    # in base_after_parse() based on the findings in deploy/stage
    # based on exploded DEPENDS???

    # Get complete specification of package that provides 'dep', in
    # the form PACKAGE_ARCH/PACKAGE-PV-PR
    pkg = bb.data.getVar('PKGPROVIDER_%s'%dep, d, 0)
    if not pkg:
        bb.error('PKGPROVIDER_%s not defined!'%dep)
        return

    filename = os.path.join(bb.data.getVar('STAGE_DEPLOY_DIR', d, True), pkg + '.tar')
    if not os.path.isfile(filename):
        bb.error('could not find %s to satisfy %s'%(filename, dep))
        return

    bb.note('unpacking %s to %s'%(filename, os.getcwd()))

    # FIXME: do error handling on tar command
    os.system('tar xf %s'%filename)
    return

python do_set_stage () {
    import bb

    recdepends = bb.data.getVar('RECDEPENDS', d, True).split()
    bb.debug('set_stage: RECDEPENDS=%s'%recdepends)
    for dep in recdepends:
        set_stage_add(dep, d)
}
do_set_stage[cleandirs] = "${STAGE_DIR}"
do_set_stage[dirs] = "${STAGE_DIR}"
addtask set_stage before do_fetch
do_set_stage[recdeptask] = "do_stage_package_build"


addtask fetch
do_fetch[dirs] = "${DL_DIR}"
python base_do_fetch() {
	import sys

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

	src_uri = bb.data.getVar('SRC_URI', localdata, 1)
	if not src_uri:
		return 1

	try:
		bb.fetch.init(src_uri.split(),d)
	except bb.fetch.NoMethodError:
		(type, value, traceback) = sys.exc_info()
		raise bb.build.FuncFailed("No method: %s" % value)

	try:
		bb.fetch.go(localdata)
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

	return
}

addtask fetchall after do_fetch
do_fetchall[recrdeptask] = "do_fetch"
base_do_fetchall() {
	:
}

addtask checkuri
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

addtask checkuriall after do_checkuri
do_checkuriall[recrdeptask] = "do_checkuri"
do_checkuriall[nostamp] = "1"
base_do_checkuriall() {
	:
}

addtask buildall after do_build
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

addtask unpack after do_fetch
do_unpack[dirs] = "${WORKDIR}"
python base_do_unpack() {
	import re

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

	src_uri = bb.data.getVar('SRC_URI', localdata, True)
	if not src_uri:
		return

	for url in src_uri.split():
		try:
			local = bb.data.expand(bb.fetch.localpath(url, localdata), localdata)
		except bb.MalformedUrl, e:
			raise FuncFailed('Unable to generate local path for malformed uri: %s' % e)
		local = os.path.realpath(local)
		ret = oe_unpack_file(local, localdata, url)
		if not ret:
			raise bb.build.FuncFailed()
}

METADATA_BRANCH ?= "${@base_detect_branch(d)}"
METADATA_REVISION ?= "${@base_detect_revision(d)}"

def base_detect_revision(d):
	path = base_get_scmbasepath(d)

	scms = [base_get_metadata_git_revision, \
			base_get_metadata_svn_revision]

	for scm in scms:
		rev = scm(path, d)
		if rev <> "<unknown>":
			return rev

	return "<unknown>"	

def base_detect_branch(d):
	path = base_get_scmbasepath(d)

	scms = [base_get_metadata_git_branch]

	for scm in scms:
		rev = scm(path, d)
		if rev <> "<unknown>":
			return rev.strip()

	return "<unknown>"	
	
	

def base_get_scmbasepath(d):
	path_to_bbfiles = bb.data.getVar( 'BBFILES', d, 1 ).split()
	return path_to_bbfiles[0][:path_to_bbfiles[0].rindex( "recipes" )]

def base_get_metadata_monotone_branch(path, d):
	monotone_branch = "<unknown>"
	try:
		monotone_branch = file( "%s/_MTN/options" % path ).read().strip()
		if monotone_branch.startswith( "database" ):
			monotone_branch_words = monotone_branch.split()
			monotone_branch = monotone_branch_words[ monotone_branch_words.index( "branch" )+1][1:-1]
	except:
		pass
	return monotone_branch

def base_get_metadata_monotone_revision(path, d):
	monotone_revision = "<unknown>"
	try:
		monotone_revision = file( "%s/_MTN/revision" % path ).read().strip()
		if monotone_revision.startswith( "format_version" ):
			monotone_revision_words = monotone_revision.split()
			monotone_revision = monotone_revision_words[ monotone_revision_words.index( "old_revision" )+1][1:-1]
	except IOError:
		pass
	return monotone_revision

def base_get_metadata_svn_revision(path, d):
	revision = "<unknown>"
	try:
		revision = file( "%s/.svn/entries" % path ).readlines()[3].strip()
	except IOError:
		pass
	return revision

def base_get_metadata_git_branch(path, d):
	branch = os.popen('cd %s; git branch | grep "^* " | tr -d "* "' % path).read()

	if len(branch) != 0:
		return branch
	return "<unknown>"

def base_get_metadata_git_revision(path, d):
	rev = os.popen("cd %s; git log -n 1 --pretty=oneline --" % path).read().split(" ")[0]
	if len(rev) != 0:
		return rev
	return "<unknown>"

GIT_CONFIG = "${STAGING_DIR_NATIVE}/usr/etc/gitconfig"

def generate_git_config(e):
        from bb import data

        if data.getVar('GIT_CORE_CONFIG', e.data, True):
                gitconfig_path = bb.data.getVar('GIT_CONFIG', e.data, True)
                proxy_command = "    gitproxy = %s\n" % data.getVar('GIT_PROXY_COMMAND', e.data, True)

                bb.mkdirhier(bb.data.expand("${STAGING_DIR_NATIVE}/usr/etc/", e.data))
                if (os.path.exists(gitconfig_path)):
                        os.remove(gitconfig_path)

                f = open(gitconfig_path, 'w')
                f.write("[core]\n")
                ignore_hosts = data.getVar('GIT_PROXY_IGNORE', e.data, True).split()
                for ignore_host in ignore_hosts:
                        f.write("    gitproxy = none for %s\n" % ignore_host)
                f.write(proxy_command)
                f.close

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
		statusvars = ['BB_VERSION', 'METADATA_BRANCH', 'METADATA_REVISION', 'MACHINE', 'MACHINE_CPU', 'MACHINE_OS', 'SDK_CPU', 'SDK_OS', 'DISTRO', 'DISTRO_VERSION']
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

        if name == "ConfigParsed":
                generate_git_config(e)

	if not data in e.__dict__:
		return NotHandled

	log = data.getVar("EVENTLOG", e.data, 1)
	if log:
		logfile = file(log, "a")
		logfile.write("%s\n" % msg)
		logfile.close()

	return NotHandled
}

addtask configure after do_unpack do_patch
do_configure[dirs] = "${S} ${B}"
#do_configure[deptask] = "do_populate_sysroot"
base_do_configure() {
	:
}

addtask compile after do_configure
do_compile[dirs] = "${S} ${B}"
base_do_compile() {
	if [ -e Makefile -o -e makefile ]; then
		oe_runmake || die "make failed"
	else
		oenote "nothing to compile"
	fi
}


sysroot_stage_dir() {
	src="$1"
	dest="$2"
	# This will remove empty directories so we can ignore them
	rmdir "$src" 2> /dev/null || true
	if [ -d "$src" ]; then
		mkdir -p "$dest"
		cp -fpPR "$src"/* "$dest"
	fi
}

sysroot_stage_libdir() {
	src="$1"
	dest="$2"

	olddir=`pwd`
	cd $src
	las=$(find . -name \*.la -type f)
	cd $olddir
	echo "Found la files: $las"		 
	for i in $las
	do
		sed -e 's/^installed=yes$/installed=no/' \
		    -e '/^dependency_libs=/s,${WORKDIR}[[:alnum:]/\._+-]*/\([[:alnum:]\._+-]*\),${STAGING_LIBDIR}/\1,g' \
		    -e "/^dependency_libs=/s,\([[:space:]']\)${libdir},\1${STAGING_LIBDIR},g" \
		    -i $src/$i
	done
	sysroot_stage_dir $src $dest
}

sysroot_stage_dirs() {
	from="$1"
	to="$2"

	sysroot_stage_dir $from${includedir} $to${STAGING_INCDIR}
	if [ "${BUILD_SYS}" = "${HOST_SYS}" ]; then
		sysroot_stage_dir $from${bindir} $to${STAGING_DIR_HOST}${bindir}
		sysroot_stage_dir $from${sbindir} $to${STAGING_DIR_HOST}${sbindir}
		sysroot_stage_dir $from${base_bindir} $to${STAGING_DIR_HOST}${base_bindir}
		sysroot_stage_dir $from${base_sbindir} $to${STAGING_DIR_HOST}${base_sbindir}
		sysroot_stage_dir $from${libexecdir} $to${STAGING_DIR_HOST}${libexecdir}
		sysroot_stage_dir $from${sysconfdir} $to${STAGING_DIR_HOST}${sysconfdir}
	fi
	if [ -d $from${libdir} ]
	then
		sysroot_stage_libdir $from/${libdir} $to${STAGING_LIBDIR}
	fi
	if [ -d $from${base_libdir} ]
	then
		sysroot_stage_libdir $from${base_libdir} $to${STAGING_DIR_HOST}${base_libdir}
	fi
	sysroot_stage_dir $from${datadir} $to${STAGING_DATADIR}
}



addtask install after do_compile
do_install[dirs] = "${D} ${S} ${B}"
# Remove and re-create ${D} so that is it guaranteed to be empty
do_install[cleandirs] = "${D}"

base_do_install() {
	:
}

base_do_package() {
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
addtask install_fixup after do_install before do_package_install

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



#addtask build after do_populate_sysroot
addtask build after do_install
do_build = ""
do_build[func] = "1"

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


python () {
    base_after_parse(d)
}

def check_app_exists(app, d):
	from bb import which, data

	app = data.expand(app, d)
	path = data.getVar('PATH', d, 1)
	return len(which(path, app)) != 0


# Patch handling
inherit patch

# Autoconf sitefile handling
inherit siteinfo

EXPORT_FUNCTIONS do_clean do_fetch do_unpack do_configure do_compile do_install

MIRRORS[func] = "0"
MIRRORS () {
${DEBIAN_MIRROR}/main	http://snapshot.debian.net/archive/pool
${DEBIAN_MIRROR}	ftp://ftp.de.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.au.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.cl.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.hr.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.fi.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.hk.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.hu.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.ie.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.it.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.jp.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.no.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.pl.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.ro.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.si.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.es.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.se.debian.org/debian/pool
${DEBIAN_MIRROR}	ftp://ftp.tr.debian.org/debian/pool
${GNU_MIRROR}	ftp://mirrors.kernel.org/gnu
${GNU_MIRROR}	ftp://ftp.matrix.com.br/pub/gnu
${GNU_MIRROR}	ftp://ftp.cs.ubc.ca/mirror2/gnu
${GNU_MIRROR}	ftp://sunsite.ust.hk/pub/gnu
${GNU_MIRROR}	ftp://ftp.ayamura.org/pub/gnu
${KERNELORG_MIRROR}	http://www.kernel.org/pub
${KERNELORG_MIRROR}	ftp://ftp.us.kernel.org/pub
${KERNELORG_MIRROR}	ftp://ftp.uk.kernel.org/pub
${KERNELORG_MIRROR}	ftp://ftp.hk.kernel.org/pub
${KERNELORG_MIRROR}	ftp://ftp.au.kernel.org/pub
${KERNELORG_MIRROR}	ftp://ftp.jp.kernel.org/pub
ftp://ftp.gnupg.org/gcrypt/     ftp://ftp.franken.de/pub/crypt/mirror/ftp.gnupg.org/gcrypt/
ftp://ftp.gnupg.org/gcrypt/     ftp://ftp.surfnet.nl/pub/security/gnupg/
ftp://ftp.gnupg.org/gcrypt/     http://gulus.USherbrooke.ca/pub/appl/GnuPG/
ftp://dante.ctan.org/tex-archive ftp://ftp.fu-berlin.de/tex/CTAN
ftp://dante.ctan.org/tex-archive http://sunsite.sut.ac.jp/pub/archives/ctan/
ftp://dante.ctan.org/tex-archive http://ctan.unsw.edu.au/
ftp://ftp.gnutls.org/pub/gnutls ftp://ftp.gnutls.org/pub/gnutls/
ftp://ftp.gnutls.org/pub/gnutls ftp://ftp.gnupg.org/gcrypt/gnutls/
ftp://ftp.gnutls.org/pub/gnutls http://www.mirrors.wiretapped.net/security/network-security/gnutls/
ftp://ftp.gnutls.org/pub/gnutls ftp://ftp.mirrors.wiretapped.net/pub/security/network-security/gnutls/
ftp://ftp.gnutls.org/pub/gnutls http://josefsson.org/gnutls/releases/
http://ftp.info-zip.org/pub/infozip/src/ http://mirror.switch.ch/ftp/mirror/infozip/src/
http://ftp.info-zip.org/pub/infozip/src/ ftp://sunsite.icm.edu.pl/pub/unix/archiving/info-zip/src/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://ftp.cerias.purdue.edu/pub/tools/unix/sysutils/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://ftp.tau.ac.il/pub/unix/admin/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://ftp.cert.dfn.de/pub/tools/admin/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://ftp.fu-berlin.de/pub/unix/tools/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://ftp.kaizo.org/pub/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://ftp.tu-darmstadt.de/pub/sysadmin/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://ftp.tux.org/pub/sites/vic.cc.purdue.edu/tools/unix/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://gd.tuwien.ac.at/utils/admin-tools/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://sunsite.ualberta.ca/pub/Mirror/lsof/
ftp://lsof.itap.purdue.edu/pub/tools/unix/lsof/  ftp://the.wiretapped.net/pub/security/host-security/lsof/
http://www.apache.org/dist  http://archive.apache.org/dist
ftp://.*/.*     http://mirrors.openembedded.org/
https?$://.*/.* http://mirrors.openembedded.org/
ftp://.*/.*     http://sources.openembedded.org/
https?$://.*/.* http://sources.openembedded.org/

}
