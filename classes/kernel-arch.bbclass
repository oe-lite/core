# -*- mode:python; -*-
#
# Set the ARCH environment variable for kernel compilation (including
# modules). Return value must match one of the architecture directories
# in the kernel source "arch" directory
#

KERNEL_ARCHS = "alpha arm avr32 blackfin cris frv h8300 ia64 m32r \
    m68k m68knommu microblaze mips mn10300 parisc powerpc s390 score sh \
    sparc um x86 xtensa"
KERNEL_ARCHS[nohash] = "1"

KERNEL_ARCH = "${@map_kernel_arch('${TARGET_ARCH}', '${KERNEL_ARCHS}')}"

def map_kernel_arch(arch, valid_archs):
    import bb, re

    arch = re.split('-', arch)[0]
    valid_archs = valid_archs.split()

    if   re.match('(i.86|athlon)$', arch):  return 'i386'
    elif re.match('powerpc64', arch):       return 'powerpc'
    elif re.match('arm26$', arch):          return 'arm26'
    elif re.match('armeb$', arch):          return 'arm'
    elif re.match('mipsel$', arch):         return 'mips'
    elif re.match('sh(3|4)$', arch):        return 'sh'
    elif re.match('bfin', arch):            return 'blackfin'

    if arch in valid_archs:                 return arch
    else:
        bb.error("cannot map '%s' to a linux kernel architecture" % arch)

def map_uboot_arch(arch):
    if arch == "powerpc":
        return "ppc"
    return arch

UBOOT_ARCH = "${@map_uboot_arch('${KERNEL_ARCH}')}"
