require linux-deif-${PV}.inc
require deif-common-kernel.inc

# Incremental PR - bump this on changes to deif-os-initramfs to
# rebuild with new initramfs.
INC_PR = "1"

# Bump this incremental PR when deif-os-initramfs is changed so we get
# deif-os-kernel rebuilt, but not linux-deif.
PR_append = ".${INC_PR}"

DEPENDS += "deif-os-initramfs"
