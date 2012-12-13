# -*- mode:python; -*-

SRC_URI =+ "file://000-misc.config \
	    file://100-${DEFCONFIG_CPU}.config \
	    file://200-toolchain.config \
	    file://300-${DEFCONFIG_OS}.config"

DEFCONFIG_CPU				= "${TARGET_CPU}"
DEFCONFIG_CPU:TARGET_CPU_i386		= "x86"
DEFCONFIG_CPU:TARGET_CPU_i486		= "x86"
DEFCONFIG_CPU:TARGET_CPU_i586		= "x86"
DEFCONFIG_CPU:TARGET_CPU_i686		= "x86"
DEFCONFIG_CPU:TARGET_CPU_i786		= "x86"

# FIXME: find a proper solution for this gnueabi mess
DEFCONFIG_OS = "${TARGET_OS}"
DEFCONFIG_OS:TARGET_LIBC_glibc		= "linux-glibc"

_CT_KERNEL_V			= "CT_KERNEL_V"
_CT_KERNEL_V:TARGET_OS_mingw32	= "CT_W32API_V"
_CT_BINUTILS_V			= "CT_BINUTILS_V"
_CT_CC_V			= "CT_CC_V"
_CT_LIBC_V			= "CT_LIBC_${@d.getVar('CT_LIBC',1).upper()}_V"
_CT_LIBC_V:TARGET_OS_mingw32	= "CT_MINGWRT_V"
_CT_GDB_V			= "CT_GDB_V"
_CT_GMP_V			= "CT_GMP_V"
_CT_MPFR_V			= "CT_MPFR_V"
_CT_PPL_V			= "CT_PPL_V"
_CT_CLOOG_V			= "CT_CLOOG_V"
_CT_MPC_V			= "CT_MPC_V"
_CT_LIBELF_V			= "CT_LIBELF_V"
_CT_LTRACE_V			= "CT_LTRACE_V"
_CT_STRACE_V			= "CT_STRACE_V"
_CT_MINGW_PDCURSES_V		= "CT_MINGW_PDCURSES_V"
_CT_DMALLOC_V			= "CT_DMALLOC_V"

_CT_LIBC_VERSION		= "CT_LIBC_VERSION"
_CT_LIBC_VERSION:TARGET_OS_mingw32 = "CT_MINGWRT_VERSION"

AUTO_CT_BOOLEAN_VARS += "CT_CROSS"
CT_CROSS:cross			= "y"
CT_CROSS:sdk-cross		= "y"

AUTO_CT_BOOLEAN_VARS += "CT_CANADIAN"
CT_CANADIAN:canadian-cross	= "y"
CT_CANADIAN:machine		= "y"

AUTO_CT_BOOLEAN_VARS += "CT_BINUTILS_FOR_TARGET"
CT_BINUTILS_FOR_TARGET:cross	= "y"

AUTO_CT_BOOLEAN_VARS += "CT_COMP_LIBS_TARGET"
CT_COMP_LIBS_TARGET:cross	= "y"

AUTO_CT_BOOLEAN_VARS += "CT_DEBUG_gdb"

AUTO_CT_BOOLEAN_VARS += "CT_GDB_GDBSERVER"
CT_GDB_GDBSERVER:cross		= "y"

AUTO_CT_BOOLEAN_VARS += "CT_GDB_CROSS"
CT_GDB_CROSS:canadian-cross	= "y"

AUTO_CT_BOOLEAN_VARS += "CT_GDB_NATIVE"
CT_GDB_NATIVE:machine		= "y"

RECIPE_FLAGS += "toolchain_ltrace"
DEFAULT_USE_toolchain_ltrace = "1"
AUTO_CT_BOOLEAN_VARS:>USE_toolchain_ltrace = " CT_DEBUG_ltrace"
CT_DEBUG_ltrace:cross			= "y"
CT_DEBUG_ltrace:TARGET_LIBC_mingw	= ""

RECIPE_FLAGS += "toolchain_strace"
DEFAULT_USE_toolchain_strace = "1"
AUTO_CT_BOOLEAN_VARS:>USE_toolchain_strace += "CT_DEBUG_strace"
CT_DEBUG_strace:cross			= "y"
CT_DEBUG_strace:TARGET_LIBC_mingw	= ""

RECIPE_FLAGS += "toolchain_dmalloc"
AUTO_CT_BOOLEAN_VARS:>USE_toolchin_dmalloc = "CT_DEBUG_dmalloc"
CT_DEBUG_dmalloc:cross			= "y"

AUTO_CT_BOOLEAN_VARS += "CT_ARCH_ARM_MODE_THUMB"
CT_ARCH_ARM_MODE_THUMB          = "${TARGET_THUMB}"

AUTO_CT_STRING_VARS += "CT_BINUTILS_EXTRA_CONFIG_ARRAY"
CT_BINUTILS_EXTRA_CONFIG_ARRAY = "--enable-targets=${TARGET_ARCH}"
CT_BINUTILS_EXTRA_CONFIG_ARRAY:native = ""
CT_BINUTILS_EXTRA_CONFIG_ARRAY:sdk-cross = ""
CT_BINUTILS_EXTRA_CONFIG_ARRAY:sdk = ""

AUTO_CT_STRING_VARS += "CT_BUILD"
CT_BUILD			= "${BUILD_ARCH}"

AUTO_CT_STRING_VARS += "CT_BUILD_PREFIX"
CT_BUILD_PREFIX			= "${BUILD_PREFIX}"

AUTO_CT_STRING_VARS += "CT_HOST"
CT_HOST				= ""
CT_HOST:machine			= "${HOST_ARCH}"
CT_HOST:sdk			= "${HOST_ARCH}"
CT_HOST:canadian-cross		= "${HOST_ARCH}"

AUTO_CT_STRING_VARS += "CT_HOST_PREFIX"
CT_HOST_PREFIX			= ""
CT_HOST_PREFIX:machine		= "${HOST_PREFIX}"
CT_HOST_PREFIX:sdk		= "${HOST_PREFIX}"
CT_HOST_PREFIX:canadian-cross	= "${HOST_PREFIX}"

AUTO_CT_STRING_VARS += "CT_TARGET_PREFIX"
CT_TARGET_PREFIX		= "${TARGET_PREFIX}"
CT_TARGET_PREFIX:native		= ""

AUTO_CT_STRING_VARS += "CT_PREFIX_DIR"
CT_PREFIX_DIR = "${D}"

AUTO_CT_STRING_VARS += "CT_TARGET_VENDOR"
CT_TARGET_VENDOR		= "${TARGET_VENDOR}"

AUTO_CT_STRING_VARS += "CT_TARGET_PREFIX"
CT_TARGET_PREFIX		= "${TARGET_PREFIX}"

AUTO_CT_STRING_VARS += "CT_TARGET_CFLAGS"
CT_TARGET_CFLAGS		= "${TARGET_CFLAGS_OPT}"

AUTO_CT_STRING_VARS += "CT_ARCH_ARCH"
CT_ARCH_ARCH			= "${TARGET_MARCH}"

AUTO_CT_STRING_VARS += "CT_ARCH_CPU"
CT_ARCH_CPU			= "${TARGET_MCPU}"

AUTO_CT_STRING_VARS += "CT_ARCH_TUNE"
CT_ARCH_TUNE			= "${TARGET_MTUNE}"

AUTO_CT_STRING_VARS += "CT_LOCAL_PATCH_DIR"
CT_LOCAL_PATCH_DIR		= "${S}"

addhook gcc_select_gdb to post_recipe_parse first after set_useflags
def gcc_select_gdb(d):
    for var in ("CT_GDB_GDBSERVER", "CT_GDB_CROSS", "CT_GDB_NATIVE"):
        if d.get(var):
            d.set("CT_DEBUG_gdb", "y")
            break

do_configure[cleandirs] = "${B}"
do_configure[dirs] = "${B}"
do_configure () {
        cp defconfig .config
        ct-ng oldconfig
}

do_configure[prefuncs] += "do_configure_defconfig"
def do_configure_defconfig(d):
    # Read in defconfig parts
    defconfig = ""
    for filename in sorted(glob.glob(d.get("SRCDIR") + "/???-*.config")):
        print "adding", filename
        with open(filename) as defconfig_file:
            defconfig += defconfig_file.read()

    rewrites = []

    for var in (d.get("AUTO_CT_BOOLEAN_VARS") or "").split():
        val = d.get(var)
        if val == 'y' or val == '1':
            rewrites.append((var, "y"))

    for var in (d.get("AUTO_CT_STRING_VARS") or "").split():
        val = d.get(var) or ""
        rewrites.append((var, '"%s"'%(val)))

    rewrites += [
        ("CT_LIBC_%s"%(d.get("CT_LIBC")), "y"),
        ("CT_EGLIBC_OPT_SIZE",
         ["n", "y"]["-Os" in (d.get("TARGET_CFLAGS") or "").split()]),
        ]

    target_fpu = d.get("TARGET_FPU")
    if target_fpu and target_fpu != "0":
        rewrites.append(("CT_ARCH_FPU", '"%s"'%(target_fpu)))

    rewrites += [
       ("CT_ARCH_FLOAT_SW",
        ["n","y"][(d.get("TARGET_FLOAT") == "soft")]),
       ("CT_ARCH_FLOAT_HW",
        ["n","y"][(d.get("TARGET_FLOAT") == "hard")]),
       ("CT_ARCH_FLOAT_SOFTFP",
        ["n","y"][(d.get("TARGET_FLOAT") == "softfp")]),
       ]

    ct_parallel_jobs = "1"
    ct_load = "0"
    parallel_make = d.get("PARALLEL_MAKE")
    if parallel_make:
        match = re.match(r"(.* |)(-j *|--jobs=)(\d+)", parallel_make)
        if match:
            ct_parallel_jobs = match.group(3)
        # FIXME: add support for parsing -l/--load-average argument
    print "parallel jobs", ct_parallel_jobs
    rewrites.append(("CT_PARALLEL_JOBS", "%s"%(ct_parallel_jobs)))
    rewrites.append(("CT_LOAD", "%s"%(ct_load)))

    def version_rewrite(component):
        version = d.get("CT_%s_VERSION"%(component.upper(),))
        assert isinstance(version, str)
        version = re.sub(r"[.\-]", "_", version)
        version_prefix = d.get("_CT_%s_V"%(component.upper(),))
        assert isinstance(version_prefix, str)
        version_var = (d.get("_CT_%s_VERSION"%(component.upper())) or
                       "CT_%s_VERSION"%(component.upper()))
        assert isinstance(version_var, str)
        print "version_rewrite %r"%((version_var, version_prefix + "_" + version, "y"),)
        return (version_var, version_prefix + "_" + version, "y")

    ct_kernel_version = d.get("CT_KERNEL_VERSION")
    if ct_kernel_version == "custom":
        rewrites.append(("CT_KERNEL_VERSION", None))
        rewrites.append(("CT_KERNEL_LINUX_USE_CUSTOM_HEADERS", "y"))
        rewrites.append(("CT_KERNEL_LINUX_CUSTOM_PATH",
                        '"%s%s/.."'%(d.get("TARGET_SYSROOT"),
                                     d.get("target_includedir"))))
    else:
        rewrites.append(version_rewrite("kernel"))
        rewrites.append(("CT_KERNEL_LINUX_INSTALL", "y"))

    for component in ("cc", "binutils", "libc", "gdb", "gmp", "mpfr", "mpc",
                      "ppl", "cloog", "libelf", "ltrace", "strace",
                      "mingw_pdcurses", "dmalloc"):
        rewrites.append(version_rewrite(component))

    ct_libc = d.get("CT_LIBC")
    if ct_libc in ("glibc", "eglibc"):
        kernel_version = d.get("CT_KERNEL_VERSION")
        libc_min_kernel_version = d.get("CT_LIBC_GLIBC_MIN_KERNEL_VERSION")
        if kernel_version != libc_min_kernel_version:
            rewrites += [
                ("CT_LIBC_GLIBC_KERNEL_VERSION_AS_HEADERS", "n"),
                ("CT_LIBC_GLIBC_KERNEL_VERSION_CHOSEN", "y"),
                ("CT_LIBC_GLIBC_MIN_KERNEL_VERSION",
                 '"%s"'%(libc_min_kernel_version)),
                ("CT_LIBC_GLIBC_MIN_KERNEL",
                 '"%s"'%(libc_min_kernel_version)),
                ]
        else:
            rewrites += [
                ("CT_LIBC_GLIBC_KERNEL_VERSION_AS_HEADERS", "y"),
                ("CT_LIBC_GLIBC_KERNEL_VERSION_CHOSEN", "n"),
                ("CT_LIBC_GLIBC_MIN_KERNEL_VERSION", None),
                ]

    if (d.get("SDK_STATIC") and
        d.get("HOST_TYPE") == "sdk" and d.get("HOST_OS") != "mingw32"):
        rewrites.append(("CT_STATIC_TOOLCHAIN","y"))

    for rewrite in rewrites:
        reobj = re.compile(r"^(#[ \t]*)?%s([ \t=][^\n]*)?$"%(rewrite[0]),
                           re.MULTILINE)
        assert len(rewrite) in (2, 3)
        if len(rewrite) == 2 and rewrite[1] is None:
            repl = "# %s is not set"%(rewrite[0])
        else:
            var = rewrite[-2]
            val = rewrite[-1]
            repl = "%s=%s"%(var, val)
        defconfig = reobj.sub(repl, defconfig, count=1)

    # Write out the mangled defconfig
    with open("defconfig", "w") as defconfig_file:
        defconfig_file.write(defconfig)

# FIXME: should we strip the -Wl, off TARGET_LDFLAGS ??
#    -e 's%\(CT_TARGET_LDFLAGS\)=.*%\1="${TARGET_LDFLAGS}"%'

do_configure[postfuncs] += "do_configure_qa"
def do_configure_qa(d):
    ok = True
    with open(".config") as dot_config:
        config = dot_config.read()

    def check_version(var_name, desired_version=None):
        errmsg = None
        if desired_version is None:
            desired_version = d.get(var_name)
        configured_version = re.search(
            re.compile(r'^%s="(.*)"$'%(var_name), re.MULTILINE), config)
        if not configured_version:
            warningmsg = "%s not found"%(var_name)
            bb.warn(warningmsg)
            return True
        elif configured_version.group(1) != desired_version:
            errmsg = "%s = %s (!= %s)"%(
                var_name, configured_version.group(1), desired_version)
        else:
            return True
        bb.error(errmsg)
        return False

    kernel_version = d.get("CT_KERNEL_VERSION")
    if kernel_version != "custom":
        ok = ok and check_version(d.get("_CT_KERNEL_V") + "ERSION",
                                  kernel_version)
    ok = ok and check_version("CT_BINUTILS_VERSION")
    ok = ok and check_version("CT_CC_VERSION")
    ok = ok and check_version(d.get("_CT_LIBC_VERSION"),
                              d.get("CT_LIBC_VERSION"))
    if d.get("CT_DEBUG_gdb"):
        ok = ok and check_version("CT_GDB_VERSION")
    if d.get("CT_USE_GMP"):
        ok = ok and check_version("CT_GMP_VERSION")
    if d.get("CT_USE_MPFR"):
        ok = ok and check_version("CT_MPFR_VERSION")
    if d.get("CT_USE_MPC"):
        ok = ok and check_version("CT_MPC_VERSION")
    if d.get("CT_USE_PPL"):
        ok = ok and check_version("CT_PPL_VERSION")
    if d.get("CT_USE_CLOOG"):
        ok = ok and check_version("CT_CLOOG_VERSION")
    if d.get("CT_USE_LIBELF"):
        ok = ok and check_version("CT_LIBELF_VERSION")
    if d.get("CT_DEBUG_ltrace"):
        ok = ok and check_version("CT_LTRACE_VERSION")
    if d.get("CT_DEBUG_strace"):
        ok = ok and check_version("CT_STRACE_VERSION")
    if d.get("CT_USE_PDCURSES"):
        ok = ok and check_version("CT_MINGW_PDCURSES_VERSION")
    if d.get("CT_DEBUG_dmalloc"):
        ok = ok and check_version("CT_DMALLOC_VERSION")
    return ok
