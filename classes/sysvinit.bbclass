#
# OE-lite class for handling sysvinit style init scripts and symlinks
#

addtask install_sysvinit after do_install before do_fixup
do_install_sysvinit[dirs] = "${D}"

sysvinit_install_script () {
	install -d ${D}${sysconfdir}/init.d
	install -m 0755 $1 ${D}${sysconfdir}/init.d/$2
}

RDEPENDS_${PN}:>USE_sysvinit = " sysvinit"

CLASS_FLAGS += "sysvinit"

python do_install_sysvinit () {
    import os

    if not d.get("USE_sysvinit"):
        return

    options = ((d.get("RECIPE_FLAGS") or "").split() +
               (d.get("CLASS_FLAGS") or "").split())
    sysconfdir = d.get("sysconfdir")

    for option in options:

        if option.endswith("_sysvinit_start"):
            start_symlink = True
        elif option.endswith("_sysvinit_stop"):
            start_symlink = False
        else:
            continue
        
        prio = d.get("USE_" + option)
        if not prio:
            continue

        if start_symlink:
            name = option[0:-len("_sysvinit_start")]
        else:
            name = option[0:-len("_sysvinit_stop")]

        script = d.get("SYSVINIT_SCRIPT_" + name)
        if not script:
            script = name.replace("_", "-")

        src = "../init.d/%s"%(script)
        if start_symlink:
            dst_dir = ".%s/rcS.d"%(sysconfdir)
            dst_base = dst_dir + "/S"
        else:
            dst_dir = ".%s/rc0.d"%(sysconfdir)
            dst_base = dst_dir + "/K"
        dst = dst_base + prio + script
        script = ".%s/init.d/%s"%(sysconfdir, script)

        if not os.path.exists(script):
            bb.note("sysvinit script not found: %s"%script)
            continue

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        if os.path.exists(dst):
            os.remove(dst)
        os.symlink(src, dst)
}
