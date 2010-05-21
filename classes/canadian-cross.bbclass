RECIPE_TYPE			 = "canadian-cross"
#
RECIPE_ARCH			 = "canadian/${SDK_ARCH}--${MACHINE_ARCH}"
RECIPE_ARCH_MACHINE		 = "canadian/${SDK_ARCH}--${MACHINE}"

PACKAGES_append		+= "${SYSROOT_PACKAGES}"
SYSROOT_PACKAGES	?= ""

# Get both sdk and machine cross toolchains and sysroots
DEFAULT_DEPENDS += "${TARGET_ARCH}/toolchain ${TARGET_ARCH}/sysroot-dev"

# Set host=sdk for architecture triplet build/sdk/target
HOST_ARCH		= "${SDK_ARCH}"
HOST_CPUTYPE		= "${SDK_CPUTYPE}"
HOST_FPU		= "${SDK_FPU}"
HOST_CFLAGS		= "${SDK_CFLAGS}"
HOST_EXEEXT		= "${SDK_EXEEXT}"
HOST_PREFIX		= "${SDK_PREFIX}"
HOST_CPPFLAGS		= "${SDK_CPPFLAGS}"
HOST_OPTIMIZATION	= "${SDK_OPTIMIZATION}"
HOST_CFLAGS		= "${SDK_CFLAGS}"
HOST_CXXFLAGS		= "${SDK_CXXFLAGS}"
HOST_LDFLAGS		= "${SDK_LDFLAGS}"

# Arch tuple arguments for configure (oe_runconf in autotools.bbclass)
OECONF_ARCHTUPLE = "--build=${BUILD_ARCH} --host=${HOST_ARCH} --target=${TARGET_ARCH}"

# 
PATH_prepend = "\
${STAGE_DIR}/target/cross${stage_base_bindir}:${STAGE_DIR}/target/cross${stage_bindir}:\
${STAGE_DIR}/host/cross${stage_base_bindir}:${STAGE_DIR}/host/cross${stage_bindir}:\
${NATIVE_DIR}${stage_base_bindir}:${NATIVE_DIR}${stage_bindir}:\
"

MACHINE_SYSROOT	 = "${STAGE_DIR}/target/sysroot"
SDK_SYSROOT	 = "${STAGE_DIR}/host/sysroot"

# Override the set_stage to handle host/target split of stage dir
python do_set_stage () {
    import bb, os
    recdepends = bb.data.getVar('RECDEPENDS', d, True).split()
    bb.debug('set_stage: RECDEPENDS=%s'%recdepends)
    for dir in ('target', 'host'):
        os.mkdir(dir)
    for dep in recdepends:
        canadian_set_stage_add(dep, d)
}

def canadian_set_stage_add(dep, d):
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

    host_arch = bb.data.getVar('HOST_ARCH', d, True)
    if pkg.startswith('native/'):
        subdir = ''
    elif pkg.startswith('cross/%s/'%host_arch):
        subdir = 'host'
    elif pkg.startswith('sysroot/%s/'%host_arch):
        subdir = 'host'
    elif pkg.startswith('sysroot/%s--'%host_arch):
        subdir = 'host'
    else:
        subdir = 'target'

    filename = os.path.join(bb.data.getVar('STAGE_DEPLOY_DIR', d, True), pkg + '.tar')
    if not os.path.isfile(filename):
        bb.error('could not find %s to satisfy %s'%(filename, dep))
        return

    bb.note('unpacking %s to %s'%(filename, os.path.join(os.getcwd(), subdir)))

    # FIXME: do error handling on tar command
    cmd = 'tar xf %s'%filename
    if subdir:
        cmd = 'cd %s;%s'%(subdir, cmd)
    os.system(cmd)

    return

FIXUP_PACKAGE_ARCH = canadian_fixup_package_arch
def canadian_fixup_package_arch(d):
    arch = bb.data.getVar('RECIPE_ARCH', d, True).partition('canadian/')
    if not arch[0] and arch[1]:
        # take part after / of RECIPE_ARCH if it begins with $RECIPE_TYPE/
        # and split at the double dash
        arch = arch[2].partition('--')
        if arch[0] and arch[1] and arch[2]:
            sdk_arch = arch[0]
            machine_arch = arch[2]
    if not sdk_arch:
        sdk_arch = '${SDK_ARCH}'
        machine_arch = '${MACHINE_ARCH}'
    packages = bb.data.getVar('PACKAGES', d, True).split()
    sysroot_packages = bb.data.getVar('SYSROOT_PACKAGES', d, True).split()
    for pkg in packages:
        if not bb.data.getVar('PACKAGE_ARCH_'+pkg, d, False):
            if pkg in sysroot_packages:
                pkg_arch = 'sysroot/'+machine_arch
            else:
                pkg_arch = 'sysroot/%s--%s'%(sdk_arch, machine_arch)
            bb.data.setVar('PACKAGE_ARCH_'+pkg, pkg_arch, d)
