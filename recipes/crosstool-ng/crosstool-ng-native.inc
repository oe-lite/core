PR = "r0"

INHIBIT_DEFAULT_DEPS = "1"

inherit native

do_configure () {
	if [ -x ${S}/configure ] ; then
		cfgcmd="${S}/configure \
		    --prefix=${prefix} \
		    --bindir=${bindir} \
		    --libdir=${libdir} \
		    --docdir=${docdir} \
		    --mandir=${mandir}"
		oenote "Running $cfgcmd..."
		$cfgcmd || oefatal "configure failed"
	else
		oefatal "no configure script found"
	fi
}
