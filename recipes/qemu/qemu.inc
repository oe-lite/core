SUMMARY = "QEMU is a generic and open source machine emulator and virtualizer."
LICENSE = "GPL-2.0"

SRC_URI = "https://download.qemu.org/qemu-${PV}.tar.xz"
RECIPE_TYPES = "native"

inherit c make pkgconfig

DEPS = "libglib libgthread"

DEPENDS += "${DEPS}"
DEPENDS_${PN} += "${DEPS}"
RDEPENDS_${PN} += "${DEPS}"

EXTRA_OECONF = "--prefix=${prefix}"
EXTRA_OECONF += "--disable-guest-agent-msi"
EXTRA_OECONF += "--extra-cflags='${CFLAGS}'"

DEPS += "libbz2"
EXTRA_OECONF += "--enable-bzip2"

DEPS += "liblzo2"
EXTRA_OECONF += "--enable-lzo"

DEPS += "libusb1"
EXTRA_OECONF += "--enable-libusb"

# The emulator targets we actually compile are selected via
# appropriate USE_qemu_* flags.

inherit auto-package-utils
AUTO_PACKAGE_UTILS_DEPENDS += "${PN}"
AUTO_PACKAGE_UTILS_RDEPENDS += "${PN}"
QEMU_TARGETS = ""

RECIPE_FLAGS += "qemu_arm"
QEMU_TARGETS:>USE_qemu_arm = " arm-linux-user armeb-linux-user arm-softmmu"
AUTO_PACKAGE_UTILS:>USE_qemu_arm = " qemu-arm qemu-armeb qemu-system-arm"

RECIPE_FLAGS += "qemu_aarch64"
QEMU_TARGETS:>USE_qemu_aarch64 = " aarch64-linux-user aarch64-softmmu"
AUTO_PACKAGE_UTILS:>USE_qemu_aarch64 = " qemu-aarch64 qemu-system-aarch64"

RECIPE_FLAGS += "qemu_ppc"
QEMU_TARGETS:>USE_qemu_ppc = " ppc-linux-user ppc-softmmu"
AUTO_PACKAGE_UTILS:>USE_qemu_ppc = " qemu-ppc qemu-system-ppc"

EXTRA_OECONF += "--target-list='${QEMU_TARGETS}'"

do_configure() {
  ./configure ${EXTRA_OECONF}
}
