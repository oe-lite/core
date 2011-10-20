# -*- mode:python; -*-

RECIPE_TYPES = "native"

inherit c autotools

SRC_URI = "http://ymorin.is-a-geek.org/download/crosstool-ng/crosstool-ng-${PV}.tar.bz2"

do_configure () {
    if [ -x "${S}/configure" ] ; then
        ${S}/configure --prefix="${D}/${prefix}"
    else
        oefatal "no configure script found"
    fi
}

MAKE_DESTDIR = ""

FILES_${PN} += "${libdir}/ct-ng-*"

do_install[postfuncs] += "do_install_crosstool_ng_fixup"
do_install_crosstool_ng_fixup () {
    mv ${D}${bindir}/ct-ng \
       ${D}${bindir}/ct-ng.orig
    sed -e 's%${D}%$(shell dirname $(MAKEFILE_LIST))/..%' \
        < ${D}${bindir}/ct-ng.orig \
        > ${D}${bindir}/ct-ng
    rm ${D}${bindir}/ct-ng.orig
    chmod +x ${D}${bindir}/ct-ng
}
