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

FIXUP_FUNCS += "crosstool_ng_fixup"

crosstool_ng_fixup () {
    mv .${stage_bindir}/ct-ng \
       .${stage_bindir}/ct-ng.orig
    sed -e 's%${D}%$(shell dirname $(MAKEFILE_LIST))/..%' \
        < .${stage_bindir}/ct-ng.orig \
        > .${stage_bindir}/ct-ng
    rm .${stage_bindir}/ct-ng.orig
    chmod +x .${stage_bindir}/ct-ng
}
