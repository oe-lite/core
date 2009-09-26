#BUILD_GUESS = "${@config_guess()}"
#BUILD_GUESS = "${TMPDIR}"
BUILD_GUESS = "${@d.getVar('TMPDIR', 1)}"
BUILD_ARCH = "${@config_guess(d)}"

def config_guess (d):
    return True


#    import subprocess
#    return subprocess.Popen(["/home/esben/src/oe-bakery/oe-lite/oe-lite/scripts/config.guess"], stdout=subprocess.PIPE).communicate()[0]
