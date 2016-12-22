SRC_URI:>TARGET_CPU_x86_64 = " file://x86_64-multilib-dirnames.patch"
SRC_URI:>TARGET_CPU_aarch64 = " file://0031-Disable-the-MULTILIB_OSDIRNAMES-and-other-multilib-o.patch"

SRC_URI += "file://mingw32-path-fixup.patch"
