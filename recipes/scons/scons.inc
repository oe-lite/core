DESCRIPTION = "A Software Construction Tool"
LICENSE = "MIT"
RECIPE_TYPES = "native"

SRC_URI = "http://ftp.osuosl.org/pub/blfs/conglomeration/scons/scons-${PV}.tar.gz"

do_compile() {
    python setup.py build
}

do_install() {
    python setup.py install --prefix ${D}
}

PACKAGES += "${PN}-man"
FILES_${PN} += "/lib/scons-${PV}"
FILES_${PN}-man += "/man"
