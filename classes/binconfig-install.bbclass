require conf/oe-lite-meta.conf
STAGE_FIXUP_FUNCS += "binconfig_fixup"

python binconfig_fixup () {
        import errno

        tempdir = bb.data.getVar('TEMP_STAGE_DIR', d, True)
        import glob
        os.chdir(tempdir)
        type_dir = glob.glob('*')
        os.chdir(type_dir[0])

        sd = bb.data.getVar('STAGE_DIR', d, True)+'/'+type_dir[0]

        files = []
        try:
                filename = '.'+bb.data.getVar('binconfiglist', d, True)
                f = open(filename, "r")
                files = f.readlines()
                f.close()
                os.unlink(filename)
        except IOError as exc:
                if exc.errno == errno.ENOENT:
                        return
                else: raise Exception("binconfg %s"%(repr(exc)))

        binconfigmangle = bb.data.getVar('binconfigmangle', d, True)

        import ConfigParser
        try:
            fd = open('.'+binconfigmangle,"r")
            config = ConfigParser.ConfigParser()

            config.readfp(fd)
            fd.close()
            os.unlink('.'+binconfigmangle)
        except Exception as exc:
            raise Exception("binconfg %s"%(repr(exc)))


        prefix = config.get("paths","prefix")
        exec_prefix = config.get("paths","exec_prefix")
        datadir = config.get("paths","datadir")
        bindir = config.get("paths","bindir")
        sbindir = config.get("paths","sbindir")
        libexecdir = config.get("paths","libexecdir")
        libdir = config.get("paths","libdir")
        includedir = config.get("paths","includedir")

        STAGE_DIR = bb.data.getVar('STAGE_DIR', d, True)

        import re, fileinput,sys
        for fn in files:
                for line in fileinput.FileInput(fn.rstrip(),inplace=1):
                        line = re.sub(r'^(prefix=).*',r'\1'+sd+prefix,line)
                        line = re.sub(r'^(exec_prefix=).*',r'\1'+sd+exec_prefix,line)
                        line = re.sub(r'^(datadir=).*',r'\1'+sd+datadir,line)
                        line = re.sub(r'^(bindir=).*',r'\1'+sd+bindir,line)
                        line = re.sub(r'^(sbindir=).*',r'\1'+sd+sbindir,line)
                        line = re.sub(r'^(libexecdir=).*',r'\1'+sd+libexecdir,line)
                        line = re.sub(r'^(libdir=).*',r'\1'+sd+libdir,line)
                        line = re.sub(r'^(includedir=).*',r'\1'+sd+includedir,line)
                        # line = re.sub(r'-I'+includedir+'/',r'I'sd+includedir+'/',line)
                        # line = re.sub(r'-L'+libdir+'/',r'-L'sd+libdir+'/',line)
                        sys.stdout.write(line)
}
