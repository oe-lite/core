# BitBake class to handle CONFIG_SITE variable for GNU Autoconf
# configure scripts.  Leverage base_arch.bbclass as much as possible.

# Recipes that need to query architecture specific knowledge, such as
# endianness or word size should use functions provided by
# base_arch.bbclass, as this class is only related to actual
# CONFIG_SITE handling.

# Export CONFIG_SITE to the enviroment. Autoconf generated configure
# scripts will make use of this to determine where to load in
# variables from. This is a space seperate list of shell scripts
# processed in the order listed.
export CONFIG_SITE = "${HOST_CONFIG_SITE}"

BUILD_CONFIG_SITE	= "${@siteinfo_search(d,'${BUILD_SITEFILES}')}"
HOST_CONFIG_SITE	= "${@siteinfo_search(d,'${HOST_SITEFILES}')}"
TARGET_CONFIG_SITE	= "${@siteinfo_search(d,'${TARGET_SITEFILES}')}"

BUILD_SITEFILES		= "common\
 ${@'${BUILD_OS}'.split('-')[0]}\
 ${BUILD_OS}\
 ${BUILD_CPU}\
 ${BUILD_CPU}-${BUILD_VENDOR}\
 ${BUILD_CPU}-${BUILD_OS}\
 bit-${BUILD_WORDSIZE}\
 endian-${BUILD_ENDIAN}\
"

HOST_SITEFILES		= "common\
 ${@'${HOST_OS}'.split('-')[0]}\
 ${HOST_OS}\
 ${HOST_CPU}\
 ${HOST_CPU}-${HOST_VENDOR}\
 ${HOST_CPU}-${HOST_OS}\
 bit-${HOST_WORDSIZE}\
 endian-${HOST_ENDIAN}\
"

TARGET_SITEFILES		= "common\
 ${@'${TARGET_OS}'.split('-')[0]}\
 ${TARGET_OS}\
 ${TARGET_CPU}\
 ${TARGET_CPU}-${TARGET_VENDOR}\
 ${TARGET_CPU}-${TARGET_OS}\
 bit-${TARGET_WORDSIZE}\
 endian-${TARGET_ENDIAN}\
"

#
# Return list of sitefiles found by searching for sitefiles in the
# following directories:
#
# 1) ${BBPATH}/site
# 2) ${FILE_DIRNAME}/site
# 3) ${FILE_DIRNAME}/site-${PV}
#
# The app and version specific sitefiles can thus override the app
# specific and site wide sitefiles, and the app specific sitefiles can
# override the site wide sitefiles.
#
# TODO: could be extended with searching in stage dir, so build
# dependencies could provide sitefiles instead of piling everything
# into common files.  When building for MACHINE_ARCH, search for
# sitefiles in stage/machine/usr/share/config.site/* and each build
# dependency should then install their files into it's own config.site
# subdir.
#
# TODO: could also be extended to search in site-${PN} and site-${P}
# if needed, but will obviosly require even more file stat'ing, so
# let's wait until the need for this is demonstrated
#
def siteinfo_search(d, sitefiles):
    import bb, os
    found = []
    sitefiles = sitefiles.split()
    bbpath = bb.data.getVar('BBPATH', d, True) or ''
    file_dirname = bb.data.getVar('FILE_DIRNAME', d, True)
    pv = bb.data.getVar('PV', d, True)

    def siteinfo_search_dir(path, found):
        for filename in sitefiles:
            filepath = os.path.join(path, 'site', filename)
            if filepath not in found and os.path.exists(filepath):
                found.append(filepath)

    # 1) ${BBPATH}/site
    for path in bbpath.split(':'):
        siteinfo_search_dir(path, found)

    # 2) ${FILE_DIRNAME}/site
    siteinfo_search_dir(os.path.join(file_dirname, 'site'), found)

    # 3) ${FILE_DIRNAME}/site-${PV}
    siteinfo_search_dir(os.path.join(file_dirname, 'site-' + pv), found)

    return ' '.join(found)
