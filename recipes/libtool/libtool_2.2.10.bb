require libtool.inc

PR = "${INC_PR}.0"

SRC_URI_append_recipe-cross += "file://cross_compile.patch;patch=1"
SRC_URI_append_recipe-sdk-cross += "file://cross_compile.patch;patch=1"
