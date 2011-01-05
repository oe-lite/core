#
# OE-lite class for handling crontab files
#

addtask install_crontab after do_install before do_fixup

RECIPE_OPTIONS_append += "crontab"

require conf/crontab.conf

CRONTAB_DEFAULT_RDEPENDS = ""
CRONTAB_DEFAULT_RDEPENDS_RECIPE_OPTION_crontab = "crond"
RDEPENDS_${PN}_append += "${CRONTAB_DEFAULT_RDEPENDS}"

do_install_crontab[dirs] = "${D}"

python do_install_crontab () {
    import os

    if not bb.data.getVar('RECIPE_OPTION_crontab', d, True):
	return

    options = (bb.data.getVar('RECIPE_OPTIONS', d, True) or "").split()
    ddir = bb.data.getVar('D', d, True)
    bb.note('ddir=%s'%ddir)
    crontabdir = bb.data.getVar('crontabdir', d, True)
    crontabdir = '%s%s'%(ddir, crontabdir)
    bb.note('crontabdir=%s'%crontabdir)
    srcdir = bb.data.getVar('SRCDIR', d, True)

    for option in options:

	if not option.endswith('_crontab'):
	    continue

	when = bb.data.getVar('RECIPE_OPTION_'+option, d, True)
	if not when:
	    continue

	name = option[0:-len('_crontab')]

	crontab_file = bb.data.getVar('CRONTAB_FILE_'+name, d, True)
	if not crontab_file:
	    crontab_file = os.path.join(srcdir, name + '.crontab')

	crontab_user = bb.data.getVar('CRONTAB_USER_'+name, d, True) or 'root'

        out_filename = os.path.join(crontabdir, crontab_user +'.'+ name)

        bb.note('crontabdir=%s'%crontabdir)
	if not os.path.exists(crontabdir):
	    os.makedirs(crontabdir, mode=0755)

        with open(out_filename, 'w') as out_file:
	    with open(crontab_file) as in_file:
                for line in in_file.readlines():
                    out_file.write(when +' '+ line)
        os.chmod(out_filename, 0644)
}
