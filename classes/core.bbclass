# -*- mode:python; -*-

inherit arch
inherit utils
inherit stage
inherit patch
inherit package
inherit mirrors

# FIXME: inherit in specialized classes, so that fx. image does not have
# to have do_fetch
inherit fetch

addtask configure after do_unpack do_patch
addtask compile after do_configure
addtask install after do_compile
addtask fixup after do_install
addtask build after do_fixup
addtask buildall after do_build
addtask clean

addtask listtasks
addtask checkuri
addtask checkuriall after do_checkuri

do_build = ""
do_build[func] = "1"


# Default recipe type is machine, so other recipe type classes must
# override this, and any other recipe type defaults as needed
RECIPE_TYPE = "machine"
RE = ""

CLASS_DEPENDS = ""

#
# Import standard Python modules as well as custom OE modules
# (disabled for now...)
#

#addhandler oe_import

#
# Shell functions for printing out messages in the BitBake output
#

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
oedebug[expand] = "0"


oe_runmake() {
    if [ -z "$MAKE" ]; then MAKE=make; fi
    oenote ${MAKE} $PARALLEL_MAKE ${EXTRA_OEMAKE} "$@"
    ${MAKE} $PARALLEL_MAKE ${EXTRA_OEMAKE} "$@" || die "oe_runmake failed"
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
python do_clean() {
    """clear the build and temp directories"""
    import shutil
    workdir = d.getVar("WORKDIR", True)
    bb.note("removing " + workdir)
    shutil.rmtree(workdir)
    stampdir = d.getVar("STAMPDIR", True)
    bb.note("removing " + stampdir)
    shutil.rmtree(stampdir)
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

do_checkuriall[recadeptask] = "do_checkuri"
do_checkuriall[nostamp] = True
do_checkuriall[func] = True
do_checkuriall = ""

do_buildall[recadaptask] = "do_build"
do_buildall[func] = True
do_buildall = ""


do_configure[dirs] = "${S} ${B}"
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

FIXUP_FUNCS += "\
install_strip \
#install_refactor \
"

python do_fixup () {
    for f in (bb.data.getVar('FIXUP_FUNCS', d, 1) or '').split():
        if not d.getVarFlag(f, 'dirs'):
            d.setVarFlag(f, 'dirs', '${D}')
        bb.build.exec_func(f, d)
}
do_fixup[dirs] = "${D}"

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


# Make sure TARGET_ARCH isn't exported
# (breaks Makefiles using implicit rules, e.g. quilt, as GNU make has this
# in them, undocumented)
TARGET_ARCH[unexport] = "1"

# Make sure MACHINE isn't exported
# (breaks binutils at least)
MACHINE[unexport] = "1"

# Make sure DISTRO isn't exported
# (breaks sysvinit at least)
DISTRO[unexport] = "1"


addhook fixup_package_arch to post_recipe_parse first after base_after_parse
def fixup_package_arch(d):
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


addhook fixup_provides to post_recipe_parse first after base_after_parse
def fixup_provides(d):
    for pkg in bb.data.getVar('PACKAGES', d, True).split():
        provides = (bb.data.getVar('PROVIDES_'+pkg, d, True) or '').split()
        if not pkg in provides:
            #bb.data.setVar('PROVIDES_'+pkg, ' '.join([pkg] + provides), d)
            if provides:
                d.setVar('PROVIDES_'+pkg, d.getVar('PROVIDES_'+pkg, False) + \
                             ' ' + pkg)
            else:
                d.setVar('PROVIDES_'+pkg, pkg)


addhook base_after_parse to post_recipe_parse first
def base_after_parse(d):
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
    recipe_type = bb.data.getVar('RECIPE_TYPE', d, True)
    # Set ${RE} for use in fx. DEPENDS and RDEPENDS
    if recipe_type != "machine":
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


addhook base_detect_machine_override to post_recipe_parse first after base_after_parse
def base_detect_machine_override(d):

    # RECIPE_ARCH override detection
    recipe_arch = bb.data.getVar('RECIPE_ARCH', d, 1)
    recipe_arch_mach = d.get('RECIPE_ARCH_MACHINE', 3)

    # Scan SRC_URI for urls with machine overrides unless the package
    # sets SRC_URI_OVERRIDES_RECIPE_ARCH=0
    override = bb.data.getVar('SRC_URI_OVERRIDES_RECIPE_ARCH', d, 1)

    def srcuri_machine_override(d, srcuri):
        import bb
        import os

        machine = d.get("MACHINE")
        if not machine:
            return False
        paths = []
        # FIXME: this should use FILESPATHPKG
        #for p in [ "${P}", "${PN}", "files", "" ]:
        for p in d.get("FILESPATHPKG").split(":"):
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

    if (recipe_arch != recipe_arch_mach and override != '0' and
        srcuri_machine_override(d, d.getVar('SRC_URI'))):
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

addhook blacklist to post_recipe_parse first after base_apply_recipe_options
def blacklist(d):
    import re
    blacklist_var = (d.getVar("BLACKLIST_VAR", True) or "").split()
    blacklist_prefix = (d.getVar("BLACKLIST_PREFIX", True) or "").split()
    blacklist = "$|".join(blacklist_var) + "$"
    if blacklist_prefix:
        blacklist += "|" + "|".join(blacklist_prefix)
    if not blacklist:
        return
    sre = re.compile(blacklist)
    for var in d.keys():
        if sre.match(var):
            d.delVar(var)

inherit useflags
inherit sanity

addhook core_varname_expansion to post_recipe_parse first
def core_varname_expansion(d):
    for varname in d.keys():
        try:
            expanded_varname = d.expand(varname)
        except oelite.meta.ExpansionError as e:
            print "Unable to expand variable name:", varname
            e.print_details()
            raise Exception(42)
        if expanded_varname != varname:
            #print "foobar %s != %s"%(expanded_varname, varname)
            flags = d.get_flags(varname, prune_var_value=False)
            #print "flags =",flags
            for flag in flags:
                if flag == "__overrides":
                    overrides = flags[flag]
                    old_overrides = d.get_flag(expanded_varname, flag)
                    if not old_overrides:
                        d.set_flag(expanded_varname, flag, overrides)
                        continue
                    for type in overrides:
                        for override_name in overrides[type]:
                            old_overrides[type][override_name] = \
                                overrides[type][override_name]
                    d.set_flag(expanded_varname, flag, old_overrides)
                    continue
                d.set_flag(expanded_varname, flag, flags[flag])
            del d[varname]

REBUILDALL_SKIP[nohash] = True
RELAXED[nohash] = True
