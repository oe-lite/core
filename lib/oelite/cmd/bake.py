import oebakery
import oelite.baker
import logging


description = "Build something"


def add_parser_options(parser):
    oelite.baker.add_bake_parser_options(parser)
    parser.add_option("-d", "--debug",
                      action="store_true", default=False,
                      help="Debug the OE-lite metadata")
    return


def parse_args(options, args):
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


def run(options, args, config):
    baker = oelite.baker.OEliteBaker(options, args, config)
    return baker.bake()
