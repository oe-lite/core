#
# OE-lite class for handling runit services
#

CLASS_FLAGS += "runit"

RDEPENDS_${PN}:>USE_runit = " runit"

addtask install_runit after do_install before do_fixup
do_install_runit[dirs] = "${D}"

python do_install_runit () {
    import os, shutil, stat

    if not bb.data.getVar('USE_runit', d, True):
        return

    options = ((d.get("RECIPE_FLAGS") or "").split() +
               (d.get("CLASS_FLAGS") or "").split())
    runitservicedir = bb.data.getVar('runitservicedir', d, True)
    srcdir = bb.data.getVar('SRCDIR', d, True)

    for option in options:

        if not option.endswith('_runit'):
            continue
        
        enable = d.get("USE_"+option)
        if not enable:
            continue

	name = option[0:-len('_runit')]
        svname = bb.data.getVar('RUNIT_NAME_'+name, d, True)
        if not svname:
            svname = name.replace('_', '-')

        script = bb.data.getVar('RUNIT_SCRIPT_'+name, d, True)
        if not script:
            script = srcdir + '/' + svname + '.runit'

        dst_dir = '.%s/%s'%(runitservicedir, svname)
	dst = dst_dir + '/run'

        if not os.path.exists(script):
            bb.note('runit script not found: %s'%script)
            continue

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copy(script, dst)
	os.chmod(dst, stat.S_IRWXU|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)
}
