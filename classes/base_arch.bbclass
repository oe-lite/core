# Return canonical and cross compiler specific arch for the given arch string.
def base_arch_cross(d, arch):
    import bb
    cross_arch = base_arch_config_sub(d, arch)
    cputype = base_arch_gcc_cputype(d, arch, cross_arch)

    if cputype == cross_arch[0]:
        cross_arch[1] = 'unknown'
    else:
        cross_arch[1] = cputype
    return '-'.join(cross_arch)


# Return the canonical and cross compiler specific arch for the build host.
def base_arch_build(d):
    import bb, os
    script = base_arch_find_script(d, 'config.guess')

    try:
        guess = base_arch_split(os.popen(script).readline().strip())
    except OSError, e:
        bb.fatal('config.guess failed: '+e)
        return None

    # Replace the silly 'pc' vendor with 'unknown' to yield a result
    # comparable with base_arch_cross().
    if guess[1] == 'pc':
        guess[1] = 'unknown'

    return '-'.join(guess)


# Return the cputype argument to use with gcc (-march/-mcpu/-mtune)
# based on the given arch and the chosen gcc version.  This is the
# place for the logic to choose the correct gcc cputype argument.
def base_arch_gcc_cputype(d, arch, gnu_arch=None, gcc=None):
    import bb
    if gnu_arch == None:
        gnu_arch = base_arch_config_sub(d, arch)
    if gcc == None:
        gcc=map(int,bb.data.getVar('CT_CC_VERSION',d,True).split('.'))
    real_cputype = base_arch_real_cputype(d, arch, gnu_arch)
    arch = arch.split('-')

    if gnu_arch[0] in ('i386','i486','i586','i686','i786'):
        return real_cputype

    if gnu_arch[0] == 'x86_64':
        return real_cputype

    if gnu_arch[0] == 'powerpc':
        if real_cputype in ('e300c1', 'e300c4'):
            return '603e'
        if real_cputype in ('e300c2', 'e300c3'):
            if gcc[0] < 4 or (gcc[0] == 4 and gcc[1] < 4):
                return '603e'
            else:
                return real_cputype

# Return the cpu core of the given arch string.  This is the place to
# handle SoC to CPU core mapping and stuff.
def base_arch_real_cputype(d, arch, gnu_arch=None):
    import bb
    if gnu_arch == None:
        gnu_arch = base_arch_config_sub(d, arch)
    arch = arch.split('-')

    if gnu_arch[0] in ('i386','i486','i586','i686'):
        if gnu_arch[1] in ('pc','unknown'):
            if arch[0] != gnu_arch[0]:
                return arch[0]
            else:
                return gnu_arch[0]
        else:
            return gnu_arch[1]
    if gnu_arch[0] == 'i786':
        if gnu_arch[1] in ('pc','unknown'):
            if arch[0] != gnu_arch[0]:
                return arch[0]
            else:
                return 'pentium4'
        else:
            return gnu_arch[1]

    if gnu_arch[0] == 'x86_64':
        if gnu_arch[1] in ('pc','unknown'):
            return gnu_arch[0]
        else:
            return gnu_arch[1]

    if gnu_arch[0] == 'powerpc':
        if gnu_arch[1] == 'unknown':
            return gnu_arch[0]

        # e300 based SoCs
        if gnu_arch[1] == 'mpc8360':
            gnu_arch[1] = 'e300c1'
        if gnu_arch[1] in ('mpc8313', 'mpc8313e'):
            gnu_arch[1] = 'e300c3'

        return gnu_arch[1]

    return 'UNSUPPORTED_CPUTYPE'


def base_arch_fpu(d, arch):
    import bb
    gnu_arch = base_arch_config_sub(d, arch)
    cputype = base_arch_real_cputype(d, arch, gnu_arch)
    arch = arch.split('-')

    if gnu_arch[0] in ('i386','i486','i586','i686', 'i786'):
        return 1

    if gnu_arch[0] == 'x86_64':
        return 1

    if gnu_arch[0] == 'powerpc':
        if cputype in ('e300c1', 'e300c3', 'e300c4'):
            return 1
        return 0

    return 0


def base_arch_cflags(d, arch):
    import bb
    gnu_arch = base_arch_config_sub(d, arch)
    gcc=map(int,bb.data.getVar('CT_CC_VERSION',d,True).split('.'))
    cputype = base_arch_gcc_cputype(d,arch,gnu_arch,gcc)

    if gnu_arch[0] in ('i386','i486','i586','i686','i786'):
        return '-march=%s -mtune=%s'%(cputype, cputype)

    if gnu_arch[0] == 'x86_64':
        return '-march=%s -mtune=%s'%(cputype, cputype)

    if gnu_arch[0] == 'powerpc':
        return '-mcpu=%s -mtune=%s'%(cputype, cputype)

    return 'UNSUPPORTED_CPUFAMILY'


def base_arch_endianness(d, arch):
    import bb
    if type(arch) is str:
        arch = arch.split('-')

    if arch[0] in ('i386', 'i486', 'i586', 'i686', 'i786', 'x86_64',
                   'arm', 'bfin', 'ia64', 'mipsel', 'sh3', 'sh4'):
        return 'le'

    if arch[0] in ('powerpc', 'powerpc64', 'armeb', 'avr32', 'mips', 'sparc'):
        return 'be'

    return 'UNKNOWN_ENDIANNESS'


def base_arch_wordsize(d, arch):
    import bb
    if type(arch) is str:
        arch = arch.split('-')

    if arch[0] in ('i386', 'i486', 'i586', 'i686', 'i786', 'powerpc',
                   'arm', 'bfin', 'mipsel', 'sh3', 'sh4', 'armeb',
                   'avr32', 'mips', 'sparc'):
        return '32'

    if arch[0] in ('x86_64', 'powerpc64', 'ia64'):
        return '64'

    return 'UNKNOWN_WORDSIZE'


def base_arch_elf(d, arch):
    import bb
    gnu_arch = base_arch_config_sub(d, arch)

    if gnu_arch[0] == 'powerpc':
        return 'PowerPC or cisco 4500'

    if gnu_arch[0] == 'x86_64':
        return 'x86-64'

    if gnu_arch[0] == 'i386':
        return 'Intel 80386'

    return 'UNKNOWN_ELF'


def base_arch_exeext(d, arch):
    import bb
    gnu_arch = base_arch_config_sub(d, arch)
    if gnu_arch[2] == 'mingw32':
        return '.exe'
    return ''


def base_arch_cpu(arch):
    archtuple = base_arch_split(arch)
    if not archtuple:
        return 'INVALID'
    return archtuple[0]


def base_arch_vendor(arch):
    archtuple = base_arch_split(arch)
    if not archtuple:
        return 'INVALID'
    return archtuple[1]


def base_arch_os(arch):
    archtuple = base_arch_split(arch)
    if not archtuple:
        return 'INVALID'
    return archtuple[2]


def base_arch_split(arch):
    archtuple = arch.split('-', 2)
    if len(archtuple) == 3:
        return archtuple
    else:
        bb.error('invalid arch string: '+arch)
        return None


def base_arch_find_script(d, filename):
    try:
        scripts = globals()['base_arch_scripts']
    except KeyError:
        scripts = {}
        globals()['base_arch_scripts'] = scripts
    if not filename in scripts:
        for bbpath in bb.data.getVar('BBPATH', d, 1).split(':'):
            filepath = os.path.join(bbpath, 'scripts', filename)
            if os.path.isfile(filepath):
                bb.debug('found %s: %s'%(filename, filepath))
                scripts[filename] = filepath
                break
        if not filename in scripts:
            bb.error('could not find script: %s'%filename)
    return scripts[filename]


def base_arch_config_sub(d, arch):
    import bb, os
    script = base_arch_find_script(d, 'config.sub')

    try:
        canonical_arch = os.popen("%s %s"%(script, arch)).readline().strip()
    except OSError, e:
        bb.error('config.sub(%s) failed: %s'%(arch, e))
        return arch

    return base_arch_split(canonical_arch)
