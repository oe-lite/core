DEPENDS_GETTEXT = "gettext${RE} gettext-native libiconv${RE} libintl${RE}"
DEPENDS =+ "${DEPENDS_GETTEXT}"

EXTRA_OECONF += "--enable-nls"
