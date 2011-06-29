# -*- mode:python; -*-


oe_runmake() {
    ${MAKE} $PARALLEL_MAKE ${EXTRA_OEMAKE} $@
}
oe_runmake[exclusive] = "compile install"
MAKE ?= "make"
MAKE[exclusive] = "compile install"
EXTRA_OEMAKE = ""
EXTRA_OEMAKE[exclusive] = "compile"

do_compile() {
	do_compile_make ${EXTRA_OEMAKE_COMPILE}
}
do_compile_make[exclusive] = "compile"
EXTRA_OEMAKE_COMPILE ?= ""
EXTRA_OEMAKE_COMPILE[exclusive] = "compile"
do_compile_make() {
	if [ -e Makefile -o -e makefile ]; then
		oe_runmake || die "make failed"
	else
		oenote "nothing to compile"
	fi
}

do_install () {
	do_install_make
}
do_install_make[exclusive] = "install"
do_install_make () {
	oe_runmake ${MAKE_DESTDIR} ${EXTRA_OEMAKE_INSTALL} install
}
MAKE_DESTDIR = "DESTDIR=${D}"
EXTRA_OEMAKE_INSTALL = "install"
EXTRA_OEMAKE_INSTALL[exclusive] = "install"

