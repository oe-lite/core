import oebakery
from oelite import util
from oebakery import info
import logging
import os
import subprocess
import oelite
import bb
import glob
import sys

description = "Host preparation tool"
arguments = ()

def add_parser_options(parser):
    parser.add_option("-l", "--list",
                      action="store_true", default=False,
                      help="Show a list of known host configurations")
    parser.add_option("-p", "--printcmd",
                    action="store_true", default=False,
                      help="Print the command needed to prepare the host for OE-lite")
    parser.add_option("-d", "--debug",
                      action="store_true", default=False,
                      help="Verbose output")
    return


def parse_args(options, args):
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    if args:
        options.head = args.pop(0)
    else:
        options.head = None
    return

def get_host_configs(distro, release, config):
    if(release  == "unknown"):
        release = "none"
    logging.debug("Reading host configuration for: %s-%s", distro, release)
    oepath = config.get("OEPATH")
    logging.debug("Searching for setup in paths; %s", oepath)
    if(distro == "all"):
        path = bb.utils.which(oepath, "setup/")
        files = glob.glob(path+"*")
    else:
        files = bb.utils.which(oepath, "setup/"+distro+"_"+release)
    logging.debug("Found file(s): "+str(files))
    return files

def determine_host(oeconfig):
    logging.debug("Running host detection")
    logging.debug("Searching for lsb_release information")
    #try lsb-release which is the most widely available method
    try:
        logging.debug("checking for the lsb_release binary")
        subprocess.call(["lsb_release"])
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            # handle file not found error.
            logging.debug("lsb_release binary not available")
        else:
            logging.debug("unhandled exception when calling lsb_release")
            raise
    else:
        try:
            logging.debug("using lsb_release to get host information")
            #strip newlines and make lowercase for later matching
            distro = oelite.util.shcmd("lsb_release -si", quiet=True)[:-1].lower()
            release = oelite.util.shcmd("lsb_release -sr", quiet=True)[:-1].lower()
        except:
            logging.debug("unhandled exception when calling lsb_release")
            raise
        else:
            logging.debug("lsb_release: distro: %s | release: %s", distro, release)
            return distro, release

    logging.debug("No lsb_release information available - checking for other known host configurations")
    logging.debug("Checking for Exherbo")
    if(os.path.exists("/etc/exherbo-release") and os.path.isfile("/etc/exherbo-release")):
        return "exherbo", "unknown"
    logging.debug("No host information for this host")
    return "unknown","unknown"

def run(options, args, config):
    logging.debug("setup.run %s", options)

    if(options.list):
        print "List of known host configurations:\n"
        hosts = get_host_configs("all", "", config)
        logging.debug("got following config files: ")
        logging.debug(hosts)
        for host in hosts:
            file = host.split("/")[-1]
            distro = file.split("_")[0]
            release = file.split("_")[1]
            print '{0:8}{1:15}{2:9}{3:15}{4:18}{5}'.format("Distro:", distro, "Release:", release,  "Setup command in: ", host)
        return 0

    #try automatic host detection
    distro, release = determine_host(config)
    if(options.printcmd):
        logging.debug("printing command for distro: %s release: %s", distro, release)
        cmd_file = get_host_configs(distro, release, config)
        cmd = open(cmd_file, 'r').read()[:-1]
        logging.debug("Command: '%s'", cmd)
        print cmd
        return 0
    if(distro == "unknown"):
        info("Your host is not known by the oe setup tool.")
        info("Try running 'oe setup -l' to see if a known configuration could match your host")
        return 0

    info("Your host configuration detected to be:\n")
    info("Distro: "+distro+"\nRelease: "+release+"\n")
    #try exact match
    cmd_file = get_host_configs(distro, release, config)
    if(not cmd_file):
        #try major version match
        cmd_file = get_host_configs(distro, release[0]+"*", config)
        if(not cmd_file):
            info("Your distribution is known, but the release can not be matched to any known configuration")
            info("Try running 'oe setup -l' to see if a known configuration could match your host")
            return 0
    cmd = open(cmd_file, 'r').read()[:-1]
    info("The following command will setup your host for OE-lite:\n")
    info(cmd)
    if os.isatty(sys.stdin.fileno()):
        while True:
            try:
                response = raw_input("\nDo you want to run this command [Yes/yes/no]? ")
            except KeyboardInterrupt:
                response = "no"
            if response in ("yes", "Yes"):
                print ""
                oelite.util.shcmd("set -ex", quiet=True)
                oelite.util.shcmd(cmd, quiet=False)
                break
            else:
                info("Not running command - answer strictly 'yes' or 'Yes' to run the command automatically")
                return 0

    return 0
