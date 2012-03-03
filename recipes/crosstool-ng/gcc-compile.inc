# -*- mode:python; -*-

# glibc configure barfs on $MACHINE
MACHINE[unexport]	= "1"

# Let Crosstool NG manage compiler and linker flags etc.
AWK[unexport]		= "1"
CC[unexport]		= "1"
CPP[unexport]		= "1"
CXX[unexport]		= "1"
F77[unexport]		= "1"
CXX[unexport]		= "1"
AR[unexport]		= "1"
NM[unexport]		= "1"
LD[unexport]		= "1"
CCLD[unexport]		= "1"
DLLTOOL[unexport]	= "1"
AS[unexport]		= "1"
OBJDUMP[unexport]	= "1"
AR[unexport]		= "1"
RANLIB[unexport]	= "1"
YACC[unexport]		= "1"
LEX[unexport]		= "1"

CFLAGS[unexport]	= "1"
CPPFLAGS[unexport]	= "1"
CXXFLAGS[unexport]	= "1"
LDFLAGS[unexport]	= "1"

CONFIG_SITE[unexport]	= "1"

inherit c++
CXX_DEPENDS:native	= ""
CXX_DEPENDS:cross	= ""
CXX_DEPENDS:sdk-cross	= ""

BLACKLIST_VAR += "LD_LIBRARY_PATH"

# FIXME: add crosstool-ng and OE-lite support for x86 -mfpmath option

do_compile[cleandirs] = "${B}/targets"
do_compile[dirs] = "${B}/targets ${B}"
do_compile () {
	if [ ! -e targets/tarballs ] ; then
		ln -s ${SRCDIR} targets/tarballs
	fi
	ct-ng build
}

