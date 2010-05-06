def base_arch_cross(d, arch):
    import bb
    arch = base_arch_config_sub(d, arch)
    (cpu, vendor, opsys) = base_arch_split(arch)
    if cpu in ('i386','i486','i586','i686','i786'):
        if vendor in ('pc','unknown'):
            vendor = 'pc'
    elif cpu == 'x86_64':
        if vendor in ('pc','unknown'):
            vendor = 'pc'
    elif cpu == 'powerpc':
        if vendor in ('e300c1','e300c3','e300c4'):
            vendor = 'fpu'
        elif vendor == 'e300c2':
            vendor = 'nofpu'
    return '%s-%s-%s'%(cpu, vendor, opsys)


def base_arch_cross_cflags(d, arch):
    import bb
    arch = base_arch_config_sub(d, arch)
    (cpu, vendor, opsys) = base_arch_split(arch)
    if cpu in ('i386','i486','i586','i686'):
        if vendor in ('pc','unknown'):
            return '-march=%s'%cpu
    elif cpu == 'i786':
        if vendor in ('pc','unknown'):
            return '-march=pentium4'
    elif cpu == 'x86_64':
        if vendor in ('pc','unknown'):
            return ''
    elif cpu == 'powerpc':
        cflags = ''
        if vendor == 'e300c1':
            return '-march=603e -mhard-float'
        if vendor == 'e300c2':
            return '-march=%s -msoft-float'%vendor
        if vendor == 'e300c3':
            return '-march=%s -mhard-float'%vendor
        if vendor == 'e300c4':
            return '-march=603e -mhard-float'
    return ''


def base_arch_exeext(d, arch):
    import bb
    arch = base_arch_config_sub(d, arch)
    (cpu, vendor, opsys) = base_arch_split(arch)
    if opsys == 'mingw32':
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


def base_arch_config_guess(d):
    import bb, os
    script = base_arch_find_script(d, 'config.guess')
    try:
        guess = os.popen(script).readline().strip()
    except OSError, e:
        bb.fatal('config.guess failed: '+e)
        return None
    (guess_cpu, guess_vendor, guess_opsys) = base_arch_split(guess)
    if guess_vendor == 'unknown':
        guess = base_arch_config_sub(d, '%s-%s'%(guess_cpu, guess_opsys))
    return guess


def base_arch_config_sub(d, arch):
    import bb, os
    script = base_arch_find_script(d, 'config.sub')
    try:
        canonical_arch = os.popen("%s %s"%(script, arch)).readline().strip()
    except OSError, e:
        bb.error('config.sub(%s) failed: %s'%(arch, e))
        return arch
    return canonical_arch
