require ${PN}.inc

# Official fixes
FIXES_SRC_URI_BASE = "http://ymorin.is-a-geek.org/download/crosstool-ng/01-fixes/${PV}/"

# Unoffcial fixes
SRC_URI += "file://glibc-march-i686.patch"

# Workaround for problems with caddr_t being defined as a macro,
# conflicting with the typedef in sys/types.h.  This breaks
# mingw32 canadian cross, but Google indicates that other packages
# has same issues, without mingw being involved.
# Prober fix for the current issue at hand might be some kind
# of fixup of the gcc/configure.ac AC_CHECK_TYPE(caddr_t)
# in gcc, but this patch is assumed generally safe.
SRC_URI += "file://glibc-typedef-caddr.patch"
