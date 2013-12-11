import oebakery
import oelite.util
import oelite.path
import logging
import os
import subprocess
import oelite
import glob
import sys
import re
import tempfile

description = "Setup host for use with this OE-lite manifest"
arguments = ()

def add_parser_options(parser):
    parser.add_option(
        '-l', '--list', action='store_true', default=False,
        help="Show a list of known host distributions")
    parser.add_option(
        '-n', '--dryrun', action='store_true', default=False,
        help="Only show the commands needed to setup the distrbution")
    parser.add_option(
        '-y', '--yes', action='store_true', default=False,
        help="Run command, without waiting for 'y' response")
    parser.add_option(
        '-d', '--debug', action='store_true', default=False,
        help="Verbose output")
    return

def parse_args(options, args):
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    return

def parse_setup_file(filename):
    name = os.path.basename(filename)
    if not re.match('[a-zA-Z].*[^#~]$', name):
        return
    if '_' in name:
        distro, release = name.split('_', 1)
    else:
        distro = name
        release = ''
    if os.path.getsize(filename) == 0:
        description = ''
        supported = False
    else:
        with open(filename, 'r') as f:
            description = f.readline()
            if not description.startswith('#'):
                logging.warning("Invalid setup file: %s", filename)
                return
            description = description.lstrip('#').strip()
            script = f.read()
            if not script.strip():
                supported = False
            else:
                supported = True
    return (name, description, supported, filename)

def get_setup_files(config):
    logging.debug("Looking for distribution setup files")
    oepath = config.get("OEPATH")
    logging.debug("Looking in: %s", oepath)
    supported_distros = {}
    unsupported_distros = {}
    found_distros = set()
    for p in oepath.split(':'):
        setup_dir = os.path.join(p, 'setup')
        if os.path.isdir(setup_dir):
            for f in glob.glob(os.path.join(setup_dir, '*')):
                setup_file = parse_setup_file(f)
                if not setup_file:
                    continue
                name, description, supported, filename = setup_file
                if name in found_distros:
                    continue
                found_distros.add(name)
                if supported:
                    supported_distros[name] = (description, filename)
                else:
                    unsupported_distros[name] = (description, filename)
    return supported_distros, unsupported_distros

def get_setup_file(config, distro, release):
    if release is None:
        name = distro
    else:
        name = '%s %s'%(distro, release)
    def retval(f):
        setup_file = parse_setup_file(f)
        if not setup_file:
            return None, None
        name, description, supported, filename = setup_file
        return filename, supported
    logging.debug("Looking for setup file for %s", name)
    oepath = config.get("OEPATH")
    logging.debug("Looking in: %s", oepath)
    # Look for release specific setup file first, falling back to common
    # versions.  When fx. searching for debian 7.1, first look for debian_7.1,
    # then debian_7.
    if release is not None:
        release_parts = release.split('.')
        for i in reversed(range(len(release_parts))):
            setup_file = oelite.path.which(oepath, os.path.join(
                    'setup', '%s_%s'%(distro, '.'.join(release_parts[:i+1]))))
            if setup_file:
                return retval(setup_file)
    # For rolling release distros, and in case a version specific setup file
    # was not found, look for version neutral setup file.
    setup_file = oelite.path.which(oepath, os.path.join('setup', distro))
    return retval(setup_file)

def get_host_distro():
    logging.debug("Running host distribution detection")
    logging.debug("Searching for lsb_release information")
    # try lsb-release which is the most widely available method
    logging.debug("Checking for the lsb_release binary")
    try:
        subprocess.call(["lsb_release"], stderr=open(os.devnull, 'w'))
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            # handle file not found error.
            logging.debug("lsb_release binary not available")
        else:
            logging.debug("Unhandled exception when calling lsb_release")
            raise
    else:
        logging.debug("Using lsb_release to get host information")
        try:
            #strip newlines and make lowercase for later matching
            distro = oelite.util.shcmd(
                "lsb_release -si", quiet=True)[:-1].lower()
            release = oelite.util.shcmd(
                "lsb_release -sr", quiet=True)[:-1].lower()
        except:
            logging.debug("Unhandled exception when calling lsb_release")
            raise
        else:
            logging.debug("lsb_release: distro=%s release=%s", distro, release)
            return distro, release

    logging.debug("No lsb_release information available")
    logging.debug("Checking for other known host distributions")
    logging.debug("Checking for Exherbo")
    if (os.path.exists("/etc/exherbo-release") and
        os.path.isfile("/etc/exherbo-release")):
        return "exherbo", None

    logging.debug("Unable to determine host distribution")
    return None, None

def run(options, args, config):
    logging.debug("setup.run %s", options)

    if(options.list):
        def list_distros(distros):
            for name in sorted(distros.keys()):
                description, filename = distros[name]
                if options.debug:
                    print "  %s (%s)"%(description, filename)
                else:
                    print "  %s"%(description)
        supported, unsupported = get_setup_files(config)
        if unsupported:
            print "\nUnsupported hosts distributions:"
            list_distros(unsupported)
        if supported:
            print "\nSupported hosts distributions:"
            list_distros(supported)
        return 0

    distro, release = get_host_distro()
    if distro is None:
        logging.error("Unable to detect host distribution")
        return 1
    print "Host distribution: %s %s"%(distro, release if release else '')

    setup_file, supported = get_setup_file(config, distro, release)
    if not setup_file:
        logging.error("Unable to find setup file for your host distribution")
        logging.error("Use 'oe setup -l' to see available setup files")
        return 1
    if not supported:
        logging.error("Setup on your host distribution is not supported")
        return 1

    logging.debug("Setup file: %s", setup_file)
    with open(setup_file, 'r') as f:
        f.readline() # skip first line, it contains setup file description
        script_body = f.read().strip()
    print "\nThe following commands %s setup your host distribution"%(
        'should' if options.dryrun else 'will')
    print '-'*79
    print script_body
    print '-'*79 + '\n'
    if options.dryrun:
        print "Run them manually, or run setup without -n/--dryrun"
        return 0

    if options.yes:
        response = 'y'
    elif os.isatty(sys.stdin.fileno()):
        while True:
            try:
                response = raw_input(
                    "Do you want to run these commands [Y/n]? ")
            except KeyboardInterrupt:
                print
                response = 'n'
            response = response.lower()
            if response == '':
                response = 'y'
            if response in ('y', 'n'):
                print
                break

    if response == 'n':
        print "Maybe another time"
        return 0
    assert response == 'y'

    script = tempfile.NamedTemporaryFile(prefix='setup.', delete=False)
    script.write("#!/bin/sh\nset -ex\n" + script_body + '\n')
    script.close()
    script = script.name
    os.chmod(script, 0755)
    success = oelite.util.shcmd(script, quiet=False)
    if success:
        os.unlink(script)
        print "\nHost is now ready to use with this OE-lite manifest"
        return 0
    else:
        return 1
