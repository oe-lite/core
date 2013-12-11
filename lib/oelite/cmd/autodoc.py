import oebakery
import oelite
import oelite.parse.docparse
import oelite.util

import logging
import os
import glob

description = "Generate documentation files from source code"
arguments = (
    ("layer", "Metadata layer(s) to generate documentation for", 0),
)

def add_parser_options(parser):
    parser.add_option(
        '-d', '--debug', action='store_true', default=False,
        help="Verbose output")
    return

def parse_args(options, args):
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    options.layers = args
    return

def run(options, args, config):
    logging.debug("autodoc.run %s", options)
    meta = oelite.meta.DictMeta(meta=config)
    def parse(filename, name, meta, index_file):
        filename = filename[len(layer)+1:]
        include_strip = (len(os.path.dirname(index_file.name))
                         - len(output_dir))
        relpath = os.path.join(layer, filename)
        output_file = os.path.join(output_dir, filename) + '.txt'
        logging.debug("autodoc parsing %s", relpath)
        parser = oelite.parse.docparse.DocParser(meta=meta)
        doc = parser.docparse(relpath, name)
        oelite.util.makedirs(os.path.dirname(output_file))
        with open(output_file, 'w') as output:
            output.write(doc.get_asciidoc())
        index_file.write("\ninclude::%s.txt[]\n"%(filename[include_strip:]))
    for layer in options.layers:
        if not os.path.exists(layer):
            logging.error("No such layer: %s", layer)
            continue
        output_dir = os.path.join(layer, 'doc', 'auto')
        oelite.util.makedirs(os.path.join(output_dir, 'recipes'))
        index_file = open(os.path.join(output_dir, 'recipes/INDEX.txt'), 'w')
        for f in sorted(glob.glob(os.path.join(layer, 'recipes/*/*.oe'))):
            name = os.path.basename(f[:-3])
            recipe_meta=meta.copy()
            if '_' in name:
                name, version = name.split('_', 1)
                recipe_meta['PN'] = name
                recipe_meta['PV'] = version
                name = " ".join((name, version))
            else:
                recipe_meta['PN'] = name
                recipe_meta['PV'] = "0"
            output_file = f[len(layer)+1:] + '.txt'
            parse(f, name, recipe_meta, index_file)
        oelite.util.makedirs(os.path.join(output_dir, 'classes'))
        index_file = open(os.path.join(output_dir, 'classes/INDEX.txt'), 'w')
        for f in sorted(glob.glob(os.path.join(layer, 'classes/*.oeclass')) +
                        glob.glob(os.path.join(layer, 'classes/*/*.oeclass'))):
            pfxlen = len(layer) + len('/classes/')
            name = f[pfxlen:-8]
            class_meta=meta.copy()
            class_meta['PN'] = "unknown"
            recipe_meta['PV'] = "0"
            output_file = os.path.join('classes', f[pfxlen:] + '.txt')
            parse(f, name, class_meta, index_file)
