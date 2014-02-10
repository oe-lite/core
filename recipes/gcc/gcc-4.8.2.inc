SRC_URI:>TARGET_CPU_x86_64 = " file://x86_64-multilib-dirnames.patch"

SRC_URI += "file://svn-205690-build-cxxflags-fix.patch"
SRC_URI += "file://svn-207171-build-cppflags-fix.patch"
SRC_URI += "file://pr-57683-parallel-build-failure.patch"
