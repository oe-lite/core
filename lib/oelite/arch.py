import oebakery
from oebakery import die, err, warn, info, debug
import os
import operator
import bb

# Handle all the arhicture related variables.

# To be able to reuse definitions for both build, machine and sdk
# architectures, the usual bitbake variables are not used, but a more
# hierarchical setup using a number of Python dictionaries.


gccspecs = {}

cpuspecs = {

    'm68k'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'b',
            'elf'		: 'ELF 32-bit MSB .*, foobar',
            },
        'mcf51'			: {
            'mcpu'		: '51',
            },
        'mcf51ac'		: {
            'mcpu'		: '51ac',
            },
        'mcf51cn'		: {
            'mcpu'		: '51cn',
            },
        'mcf51em'		: {
            'mcpu'		: '51em',
            },
        'mcf51qe'		: {
            'mcpu'		: '51qe',
            },
        'mcf5206'		: {
            'mcpu'		: '5206',
            },
        'mcf5206e'		: {
            'mcpu'		: '5206e',
            },
        'mcf5208'		: {
            'mcpu'		: '5208',
            },
        'mcf52277'		: {
            'mcpu'		: '52277',
            },
        },

    'powerpc'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'b',
            'elf'		: 'ELF 32-bit MSB .*, PowerPC or cisco 4500',
            },
        '603e'			: {
            'mcpu'		: '603e',
            'float'		: 'hard',
            },
        'e300c1'		: {
            'mcpu'		: 'e300c1',
            'float'		: 'hard',
            },
        'e300c2'		: {
            'mcpu'		: 'e300c2',
            },
        'e300c3'		: {
            'mcpu'		: 'e300c3',
            'float'		: 'hard',
            },
        'e300c4'		: {
            'mcpu'		: 'e300c4',
            'float'		: 'hard',
            },
        },

    'powerpc64'		: {
        'DEFAULT'		: {
            'wordsize'		: '64',
            'endian'		: 'b',
            },
        },

    'arm'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            'elf'		: 'ELF 32-bit LSB .*, ARM',
            'abi flags'         : [
                ['arm abi', 'eabi', {
                       'eabi' : {
                            'os' : 'eabi',
                            },
                        # Currently, OE-lite does only support EABI for
                        # ARM. When/if OABI is added, os should be kept as
                        # linux-gnu for OABI
                        }
                 ],
                ]
            },
        '920t'			: {
            'mcpu'		: 'arm920t',
            'mtune'		: 'arm920t',
            },
        '926ejs'		: {
            'march'		: 'armv5te',
            'mcpu'		: 'arm926ej-s',
            'mtune'		: 'arm926ej-s',
            },
        '1176jzfs'		: {
             'march'		: 'armv6',
             'mcpu'		: 'arm1176jzf-s',
             'mtune'		: 'arm1176jzf-s',
             'abi flags'	: [
                ['float abi', 'hard', {
                        'hard' : {
                            'float' : 'hard',
                            'fpu'   : 'vfp',
                            },
                        'softfp' : {
                            'float' : 'softfp',
                            'fpu'   : 'vfp',
                            },
                        'soft' : {
                            'float' : 'soft',
                            },
                        }
                 ]
                ]
             },
        'cortexa7'		: {
            'mcpu'		: 'cortex-a7',
            'mtune'	 	: 'cortex-a7',
            'abi flags'         : [
                ['float abi', 'softfp', {
                        'hard' : {
                            'float' : 'hard',
                            'fpu'   : 'neon-vfpv4',
                            'vendor' : 'hf',
                            },
                        'softfp' : {
                            'float' : 'softfp',
                            'fpu'   : 'neon-vfpv4',
                            'vendor' : '',
                            },
                        'soft' : {
                            'float' : 'soft',
                            'vendor' : 'soft',
                            },
                        }
                 ],
                ['instruction set', 'thumb', {
                        'arm' : { },
                        'thumb' : {
                            'thumb' : '1',
                            'vendor' : 't',
                            },
                        }
                 ],
                ]
            },
        'cortexa8'		: {
            'mcpu'		: 'cortex-a8',
            'mtune'             : 'cortex-a8',
            'abi flags'         : [
                ['float abi', 'hard', {
                        'hard' : {
                            'float' : 'hard',
                            'fpu'   : 'neon',
                            'vendor' : 'neon',
                            },
                        'softfp' : {
                            'float' : 'softfp',
                            'fpu'   : 'neon',
                            'vendor' : 'neonsfp',
                            },
                        'soft' : {
                            'float' : 'soft',
                            'vendor' : 'sfp',
                            },
                        }
                 ],
                ['instruction set', 'thumb', {
                        'arm' : {
                            'mode' : 'arm',
                            },
                        'thumb' : {
                            'mode' : 'thumb',
                            'vendor' : 't',
                            },
                        }
                 ],
                ]
            },
        'cortexa9'		: {
            'mcpu'		: 'cortex-a9',
            'mtune'             : 'cortex-a9',
            'abi flags'         : [
                ['float abi', 'hard', {
                        'hard' : {
                            'float' : 'hard',
                            'fpu'   : 'neon',
                            'vendor' : 'neon',
                            },
                        'softfp' : {
                            'float' : 'softfp',
                            'fpu'   : 'neon',
                            'vendor' : 'neonsfp',
                            },
                        'soft' : {
                            'float' : 'soft',
                            'vendor' : 'sfp',
                            },
                        }
                 ],
                ['instruction set', 'thumb', {
                        'arm' : {
                            'mode' : 'arm',
                            },
                        'thumb' : {
                            'mode' : 'thumb',
                            'vendor' : 't',
                            },
                        }
                 ],
                ]
            },
        },

    'armeb'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'b',
            },
        },

    'avr32'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'b',
            },
        },

    'mips'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'b',
            },
        },

    'mipsel'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            },
        },

    'sparc'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'b',
            },
        },

    'bfin'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            },
        },

    'sh3'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            },
        },

    'sh4'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            },
        },

    'i386'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            'elf'		: 'ELF 32-bit LSB .*, Intel 80386',
            'march'		: 'i386',
            'fpu'		: '387',
            'float'		: 'hard',
            },
        },

    'i486'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            'elf'		: 'ELF 32-bit LSB .*, Intel 80386',
            'march'		: 'i486',
            'fpu'		: '387',
            'float'		: 'hard',
            },
        'winchipc6'		: {
            'march'		: 'winchip-c6',
            },
        'winchip2'		: {
            'march'		: 'winchip2',
            },
        },

    'i586'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            'elf'		: 'ELF 32-bit LSB .*, Intel 80386',
            'march'		: 'i586',
            'fpu'		: '387',
            'float'		: 'hard',
            },
        'mmx'			: {
            'march'		: 'pentium-mmx',
            },
        'k6'			: {
            'march'		: 'k6',
            },
        'k62'			: {
            'march'		: 'k6-2',
            },
        'geode'			: {
            'march'		: 'geode',
            },
        'c3'			: {
            'march'		: 'c3',
            },
        'c32'			: {
            'march'		: 'c3-2',
            },
        },

    'i686'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            'elf'		: 'ELF 32-bit LSB .*, Intel 80386',
            'march'		: 'i686',
            'fpu'		: '387',
            'float'		: 'hard',
            },
        'mmx'			: {
            'march'		: 'pentium2',
            },
        'sse'			: {
            'march'		: 'pentium3',
            'fpu'		: 'sse',
            },
        'sse2'			: {
            'march'		: 'pentium-m',
            'fpu'		: 'sse',
            },
        'athlon'		: {
            'march'		: 'athlon',
            },
        'athlon4'		: {
            'march'		: 'athlon-4',
            'fpu'		: 'sse',
            },
        },

    'i786'		: {
        'DEFAULT'		: {
            'wordsize'		: '32',
            'endian'		: 'l',
            'elf'		: 'ELF 32-bit LSB .*, Intel 80386',
            'march'		: 'pentium4',
            'fpu'		: 'sse',
            'float'		: 'hard',
            },
        'sse3'			: {
            'march'		: 'prescott',
            },
        },

    'x86_64'		: {
        'DEFAULT'		: {
            'wordsize'		: '64',
            'endian'		: 'l',
            'elf'		: 'ELF 64-bit LSB .*, x86-64',
            'march'		: 'opteron',
            'fpu'		: 'sse',
            'float'		: 'hard',
            },
        'sse3'			: {
            'march'		: 'k8-sse3',
            },
        'nocona'		: {
            'march'		: 'nocona',
            },
        'core2'			: {
            'march'		: 'core2',
            },
        'atom'			: {
            'march'		: 'atom',
            },
        'amdfam10'		: {
            'march'		: 'amdfam10',
            },
        },

    'ia64'		: {
        'DEFAULT'		: {
            'wordsize'		: '64',
            'endian'		: 'l',
            },
        },
    }

cpumap = {

    'powerpc'		: {
        'mpc5121e'		: 'e300c4',
        'mpc5125'		: 'e300c4',
        'mpc8313'		: 'e300c3',
        'mpc8313e'		: 'e300c3',
        'mpc8360'		: 'e300c1',
        'mpc8270'		: 'g2le',
        },

    'arm'		: {
        'at91rm9200'		: '920t',
        'at91sam9260'		: '926ejs',
        'omap3520'		: ('cortexa8', ('omap3', 'omap')),
        'omap3530'		: ('cortexa8', ('omap3', 'omap')),
        'omap4430'		: ('cortexa9neon', ('omap4', 'omap')),
        'omap4440'		: ('cortexa9neon', ('omap4', 'omap')),
        'am335x'		: ('cortexa8', 'am' ),
        'imx21'			: ('926ejs', 'imx'),
        'imx23'			: ('926ejs', 'mxs'),
        'imx25'			: ('926ejs', 'imx'),
        'imx27'			: ('926ejs', 'imx'),
        'imx28'			: ('926ejs', 'mxs'),
        'imx280'		: ('926ejs', ('imx28', 'mxs')),
        'imx281'		: ('926ejs', ('imx28', 'mxs')),
        'imx283'		: ('926ejs', ('imx28', 'mxs')),
        'imx285'		: ('926ejs', ('imx28', 'mxs')),
        'imx286'		: ('926ejs', ('imx28', 'mxs')),
        'imx287'		: ('926ejs', ('imx28', 'mxs')),
        'imx31'			: ('1136jfs', 'imx'),
        'imx35'			: ('1136jfs', 'imx'),
        'imx51'			: ('cortexa8', 'imx'),
        'imx512'		: ('cortexa8', ('imx51', 'imx')),
        'imx513'		: ('cortexa8', ('imx51', 'imx')),
        'imx514'		: ('cortexa8', ('imx51', 'imx')),
        'imx515'		: ('cortexa8', ('imx51', 'imx')),
        'imx516'		: ('cortexa8', ('imx51', 'imx')),
        'imx53'			: ('cortexa8', 'imx'),
        'imx534'		: ('cortexa8', ('imx53', 'imx')),
        'imx535'		: ('cortexa8', ('imx53', 'imx')),
        'imx536'		: ('cortexa8', ('imx53', 'imx')),
        'imx537'		: ('cortexa8', ('imx53', 'imx')),
        'imx538'		: ('cortexa8', ('imx53', 'imx')),
        'imx6'			: ('cortexa9', 'imx'),
        'ls1021a'		: ('cortexa7', ('ls102x', 'ls1', 'layerscape')),
        'imx6sl'		: ('cortexa9', ('imx6', 'imx')),
        'imx6dl'		: ('cortexa9', ('imx6', 'imx')),
        'imx6q'			: ('cortexa9', ('imx6', 'imx')),
        },

    'x86'		: {
        'celeronm575'		: (('i686', 'sse2'),),
        },

    }

osspecs = {

    'mingw32'	: {
        'exeext'		: '.exe',
        'elf'			: 'PE32 .* for MS Windows .* Intel 80386 32-bit',
        },

    }


def init(d):
    sanity(d)
    gcc_version = d.get('GCC_VERSION')
    arch_set_build_arch(d, gcc_version)
    arch_set_cross_arch(d, 'MACHINE', gcc_version)
    arch_set_cross_arch(d, 'SDK', gcc_version)
    return


def sanity(d):
    import bb
    fail = False
    sdk_cpu = d.get("SDK_CPU")
    if not sdk_cpu:
        bb.error("SDK_CPU not set")
        fail = True
    sdk_os = d.get("SDK_OS")
    if not sdk_os:
        bb.error("SDK_OS not set")
        fail = True
    machine = d.get("MACHINE")
    machine_cpu = d.get("MACHINE_CPU")
    machine_os = d.get("MACHINE_OS")
    if machine:
        pass
    elif machine_cpu and machine_os:
        pass
    elif machine_cpu:
        bb.error("MACHINE_CPU set, but not MACHINE_OS")
        fail = True
    elif machine_os:
        bb.error("MACHINE_OS set, but not MACHINE_CPU")
        fail = True
    else:
        bb.error("MACHINE or MACHINE_CPU and MACHINE_OS must be set")
        fail = True
    if fail:
        bb.fatal("Invalid MACHINE and/or SDK specification\n"
                 "Check your conf/local.conf file and/or machine and distro config files.")
    return


def update(d):
    gcc_version = d.get('GCC_VERSION')
    arch_update(d, 'BUILD', gcc_version)
    arch_update(d, 'HOST', gcc_version)
    arch_update(d, 'TARGET', gcc_version)
    return


def arch_set_build_arch(d, gcc_version):
    try:
        guess = globals()['config_guess_cache']
    except KeyError:
        #bb.debug("config.guess")
        script = arch_find_script(d, 'config.guess')
        try:
            guess = arch_split(os.popen(script).readline().strip())
        except OSError, e:
            #bb.fatal('config.guess failed: '+e)
            return None
        config_guess_cache = guess
        globals()['config_guess_cache'] = config_guess_cache

        # Replace the silly 'pc' vendor with 'unknown' to yield a result
        # comparable with arch_cross().
        if guess[1] == 'pc':
            guess[1] = 'unknown'
    guess[1] = "build_" + guess[1]
    d.set('BUILD_ARCH', '-'.join(guess))
    return


def arch_set_cross_arch(d, prefix, gcc_version):
    cross_arch = '%s-%s'%(d.get(prefix+'_CPU', True),
                          d.get(prefix+'_OS', True))
    cross_arch = arch_config_sub(d, cross_arch)
    abis = (d.get(prefix+'_ABI', True) or "").split()
    if prefix == "MACHINE":
        vendor_prefix = None
    else:
        vendor_prefix = prefix.lower() + "_"
    cross_arch = arch_fixup(cross_arch, gcc_version, abis, vendor_prefix)
    d[prefix+'_ARCH'] = cross_arch[0]
    if cross_arch[1]:
        d[prefix+'_CPU_FAMILIES'] = " ".join(cross_arch[1])
    return


def arch_update(d, prefix, gcc_version):
    arch = d.get(prefix+'_ARCH', True)
    gccspec = arch_gccspec(arch, gcc_version)
    (cpu, vendor, os) = arch_split(arch)
    d[prefix+'_CPU'] = cpu
    d[prefix+'_VENDOR'] = vendor
    d[prefix+'_OS'] = os
    ost = os.split('-',1)
    if len(ost) > 1:
        d[prefix+'_BASEOS'] = ost[0]
    else:
        d[prefix+'_BASEOS'] = ""
    for spec in gccspec:
        if spec in ("abi flags"):
            continue
        d[prefix+'_'+spec.upper()] = gccspec[spec]
    return


def arch_fixup(arch, gcc, abis, vendor_prefix=None):
    import re
    gccv=re.search('(\d+)[.](\d+)[.]?',gcc).groups()
    (cpu, vendor, os) = arch_split(arch)

    if vendor == 'pc':
        vendor = 'unknown'

    families = []
    if cpu in cpumap and vendor in cpumap[cpu]:
        mapto = cpumap[cpu][vendor]
        families = [vendor]
        if isinstance(mapto, basestring):
            vendor = mapto
        else:
            assert isinstance(mapto, tuple) and len(mapto) in (1, 2)
            if isinstance(mapto[0], basestring):
                vendor = mapto[0]
            else:
                assert isinstance(mapto[0], tuple) and len(mapto[0]) == 2
                cpu = mapto[0][0]
                vendor = mapto[0][1]
            if len(mapto) > 1:
                if isinstance(mapto[1], basestring):
                    families.append(mapto[1])
                else:
                    assert isinstance(mapto[1], tuple)
                    families.extend(mapto[1])
        families.append(vendor)

    if cpu == "powerpc":
        if vendor in ('e300c1', 'e300c4'):
            vendor = '603e'
        if vendor in ('e300c2', 'e300c3'):
            if gccv[0] < 4 or (gccv[0] == 4 and gccv[1] < 4):
                vendor = '603e'

    if cpu in cpuspecs and vendor in cpuspecs[cpu]:
        pass
    elif vendor == 'unknown':
        pass
    else:
        bb.fatal("unknown cpu vendor: %s"%vendor)
        vendor = 'unknown'

    # Merge DEFAULT and vendor abi_flags, keeping DEFAULT flags first
    abi_flags = []
    if "DEFAULT" in cpuspecs[cpu] and 'abi flags' in cpuspecs[cpu]["DEFAULT"]:
        abi_flags += cpuspecs[cpu]["DEFAULT"]["abi flags"]
    if vendor in cpuspecs[cpu] and 'abi flags' in cpuspecs[cpu][vendor]:
        for abi_flag in cpuspecs[cpu][vendor]['abi flags']:
            try:
                flag_index = map(operator.itemgetter(0), abi_flags).index(
                    abi_flag)
                abi_flags[flag_index][1] = abi_flag[1]
                for flag_value in abi_flag[2].items():
                    abi_flags[flag_index][2][flag_value[0]] = flag_value[1]
            except ValueError:
                abi_flags.append(abi_flag)

    if abi_flags:
        cpuspec = cpuspecs[cpu][vendor]
        extra_vendor = []
        extra_os = []
        for abi_flag in abi_flags:
            diff = set(abis).intersection(set(abi_flag[2]))
            if len(diff) > 1:
                bb.fatal("ABI with %s is invalid, only one of %s should be given"
                      % (', '.join(diff), ', '.join(abi_flag[2].keys())))
            if len(diff) == 1:
                abi_select = diff.pop()
                abis.remove(abi_select)
            else:
                abi_select = abi_flag[1]
            if 'vendor' in abi_flag[2][abi_select]:
                extra_vendor.append(abi_flag[2][abi_select].pop('vendor'))
            if 'os' in abi_flag[2][abi_select]:
                extra_os.append(abi_flag[2][abi_select].pop('os'))
            cpuspec.update(abi_flag[2][abi_select])
        vendor = vendor + ''.join(extra_vendor)
        os = os + ''.join(extra_os)
        cpuspecs[cpu].update({vendor : cpuspec})

    if len(abis) > 0:
        bb.fatal("ABI %s not valid for arch %s-%s-%s" %(', '.join(abis), cpu,vendor,os))

    if vendor_prefix:
        vendor = vendor_prefix + vendor

    return ('-'.join((cpu, vendor, os)), families)


def arch_gccspec(arch, gcc):
    import re
    if gcc in gccspecs:
        if arch in gccspecs[gcc]:
            return gccspecs[gcc][arch]
    else:
        gccspecs[gcc] = {}

    gccv=re.search('(\d+)[.](\d+)[.]?',gcc).groups()
    (cpu, vendor, os) = arch_split(arch)

    gccspec = {}
    if cpu in cpuspecs:
        gccspec.update(cpuspecs[cpu]['DEFAULT'])
    if cpu in cpuspecs and vendor in cpuspecs[cpu]:
        gccspec.update(cpuspecs[cpu][vendor])
    if os in osspecs:
        gccspec.update(osspecs[os])

    try:

        if gccspec['mcpu'] in ('e300c1', 'e300c4'):
            gccspec['mcpu'] = '603e'
        if gccspec['mtune'] in ('e300c1', 'e300c4'):
            gccspec['mtune'] = '603e'

        if gccspec['mcpu'] in ('e300c2', 'e300c3'):
            if gccv[0] < 4 or (gccv[0] == 4 and gccv[1] < 4):
                gccspec['mcpu'] = '603e'
        if gccspec['mtune'] in ('e300c2', 'e300c3'):
            if gccv[0] < 4 or (gccv[0] == 4 and gccv[1] < 4):
                gccspec['mtune'] = '603e'

    except KeyError, e:
        #bb.debug("KeyError in arch_gccspec: ")
        pass

    gccspecs[gcc][arch] = gccspec
    return gccspec


def arch_config_sub(d, arch):
    try:
        config_sub_cache = globals()['config_sub_cache']
    except KeyError:
        config_sub_cache = {}
        globals()['config_sub_cache'] = config_sub_cache

    try:
        canonical_arch = config_sub_cache[arch]

    except KeyError:
        script = arch_find_script(d, 'config.sub')
        try:
            bb.debug("%s %s"%(script, arch))
            canonical_arch = os.popen("%s %s"%(script, arch)).readline().strip()
            config_sub_cache[arch] = canonical_arch
        except OSError, e:
            bb.error("config.sub(%s) failed: %s"%(arch, e))
            return arch

    return canonical_arch


def arch_split(arch):
    archtuple = arch.split('-', 2)
    if len(archtuple) == 3:
        return archtuple
    else:
        bb.error('invalid arch string: '+arch)
        return None


def arch_find_script(d, filename):
    try:
        scripts = globals()['arch_scripts']
    except KeyError:
        scripts = {}
        globals()['arch_scripts'] = scripts
    if not filename in scripts:
        for oepath in d.get('OEPATH', 1).split(':'):
            filepath = os.path.join(oepath, 'scripts', filename)
            if os.path.isfile(filepath):
                #bb.debug("found %s: %s"%(filename, filepath))
                scripts[filename] = filepath
                break
        if not filename in scripts:
            bb.error('could not find script: %s'%filename)
    return scripts[filename]
