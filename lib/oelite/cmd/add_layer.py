import oebakery
import logging
import oelite.util
import oelite.git

import sys
import os
import subprocess


description = "Add layer to manifest helper tool"
arguments = (
    ("layer", "Name of the layer to add (fx. meta/qt or src/linux)", 0),
)


def add_parser_options(parser):
    parser.add_option(
        '-d', '--debug',
        action="store_true", default=False,
        help="Show debug messages")
    parser.add_option(
        '-t', '--type',
        help="Layer type (fx. meta, linux, u-boot or barebox)")
    parser.add_option(
        '-u', '--url',
        help="URL of git repository to use as layer")
    parser.add_option(
        '-b', '--branch',
        help="Branch to use as initial master branch")
    parser.add_option(
        '-c', '--commit',
        help="Commit to use as initial master branch head")
    return


def parse_args(options, args):
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    if len(args) != 1:
        return "bad argument count: %d (1 required)"%(len(args))
    options.layer = args.pop(0)
    return


def run(options, args, config):
    logging.debug("add-layer.run %s", options)
    return add_layer(options)


_dir_stack = []
def pushd(path):
    global _dir_stack
    _dir_stack.append(os.getcwd())
    os.chdir(path)

def popd():
    global _dir_stack
    os.chdir(_dir_stack.pop())


def add_layer(args):
    if not args.type:
        if args.layer.startswith('meta/'):
            args.type = 'meta'
        elif args.layer.startswith('src/'):
            if 'linux' in args.layer:
                args.type = 'linux'
            elif 'u-boot' in args.layer:
                args.type = 'u-boot'
            elif 'barebox' in args.layer:
                args.type = 'barebox'
            else:
                args.type = 'src'
        elif args.layer.startswith('lib/'):
            args.type = 'lib'
        else:
            logging.error("unable determine layer type, please use '-t'")
            sys.exit(1)
    elif args.type == 'meta' and not args.layer.startswith('meta/'):
        args.layer = os.path.join('meta', args.layer)
    elif (args.type in ('src', 'linux', 'u-boot', 'barebox')
          and not args.layer.startswith('src/')):
        args.layer = os.path.join('src', args.layer)
    elif args.type == 'lib' and not args.layer.startswith('lib/'):
        args.layer = os.path.join('lib', args.layer)
    if not args.url:
        if args.type == 'meta':
            logging.warning("URL not specified, using OE-lite.org")
            args.url = "git://oe-lite.org/oe-lite/%s.git"%(
                os.path.basename(args.layer))
        elif args.type == 'linux':
            logging.warning(
                "URL not specified, using linux-stable from Greg Kroah-Hartman")
            args.url = "git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git"
        elif args.type == 'u-boot':
            logging.warning(
                "URL not specified, using upstream from DENX")
            args.url = "git://git.denx.de/u-boot.git"
        elif args.type == 'barebox':
            logging.warning(
                "URL not specified, using upstream from Pengutronix")
            args.url = "git://git.pengutronix.de/git/barebox.git"
        else:
            logging.error("URL not specified, please use '-u'")
            sys.exit(1)
    add_submodule(args)
    if args.commit:
        # FIXME: use oelite.git module to figure out if tag or sha1
        args.src_rev = 'commit=%s'%(args.commit)
    elif args.branch:
        args.src_rev = 'branch=%s'%(args.branch)
    else:
        args.src_rev = 'branch=HEAD'
    if args.type == 'meta':
        return add_meta(args)
    elif args.type == 'linux':
        return add_linux(args)
    elif args.type == 'u-boot':
        return add_uboot(args)
    elif args.type == 'barebox':
        return add_barebox(args)


def add_linux(args):
    recipe_dir = 'recipes/linux'
    recipe_name = os.path.basename(args.layer).replace('_', '-')
    add_recipe(os.path.join(recipe_dir, '%s_git.oe'%(recipe_name)),
               "Linux recipe for building from remote git repository",
               ['kernel'], args.url, src_rev=args.src_rev)
    add_recipe(os.path.join(recipe_dir, '%s_local.oe'%(recipe_name)),
               "Linux recipe for building directly from manifest repository",
               ['kernel'], 'file://${TOPDIR}/%s', priority=-1)
    commit_recipes(args)


def add_uboot(args):
    recipe_dir = 'recipes/u-boot'
    recipe_name = os.path.basename(args.layer).replace('_', '-')
    add_recipe(os.path.join(recipe_dir, '%s_git.oe'%(recipe_name)),
               "U-Boot recipe for building from remote git repository",
               ['u-boot'], args.url, src_rev=args.src_rev)
    add_recipe(os.path.join(recipe_dir, '%s_local.oe'%(recipe_name)),
               "U-Boot recipe for building directly from manifest repository",
               ['u-boot'], 'file://${TOPDIR}/%s'%(args.layer), priority=-1)
    commit_recipes(args)


def add_barebox(args):
    recipe_dir = 'recipes/barebox'
    recipe_name = os.path.basename(args.layer).replace('_', '-')
    add_recipe(os.path.join(recipe_dir, '%s_git.oe'%(recipe_name)),
               "Barebox recipe for building from remote git repository",
               ['barebox'], args.url, src_rev=args.src_rev)
    add_recipe(os.path.join(recipe_dir, '%s_local.oe'%(recipe_name)),
               "Barebox recipe for building directly from manifest repository",
               ['barebox'], 'file://${TOPDIR}/%s'%(args.layer), priority=-1)
    commit_recipes(args)

    
def add_recipe(recipe_file, description, classes, url,
               src_rev=None, priority=None):
    if not os.path.exists(os.path.dirname(recipe_file)):
        os.makedirs(os.path.dirname(recipe_file))
    if os.path.exists(recipe_file):
        logging.warning('recipe already exists: %s', recipe_file)
        return
    if url.startswith('git://'):
        src_uri = url
    elif '://' in url:
        protocol, path = url.split('://', 1)
        src_uri = 'git://%s;protocol=%s'%(path, protocol)
    elif ':' in url:
        src_uri = 'git://%s;protocol=ssh'%(url.replace(':', '/'))
    elif url.startswith('/'):
        src_uri = 'git://%s;protocol=file'%(url)
    else:
        src_uri = 'git://${TOPDIR}/%s;protocol=file'%(url)
    src_dir = os.path.basename(url.strip('/'))
    if src_dir.endswith('.git'):
        src_dir = src_dir[:-4]
    with open(recipe_file, 'w') as recipe:
        recipe.write("## %s\n"%(description))
        recipe.write("\ninherit %s\n"%(' '.join(classes)))
        recipe.write("\nSRC_URI = %r\n"%(src_uri))
        if src_rev:
            recipe.write("SRC_URI .= ';${SRC_REV}'\nSRC_REV = %r\n"%(src_rev))
        recipe.write("S = '${SRC_DIR}/%s'\n"%(src_dir))
        if priority:
            recipe.write("\nPRIORITY = '%d'\n"%(priority))
    cmd = ['git', 'add', recipe_file]
    sts = subprocess.call(cmd)
    if sts != 0:
        logging.error("adding %s to index failed: %d", recipe_file, sts)
        sys.exit(1)


def commit_recipes(args):
    cmd = ['git', 'commit', '-m', "Add recipes for %s layer"%(args.layer)]
    logging.info("Committing recipes to manifest")
    sts = subprocess.call(cmd)
    if sts != 0:
        logging.error("committing recipes failed: %d", sts)
        sys.exit(1)


def add_meta(args):
    return


def add_submodule(args):
    if os.path.exists(args.layer):
        logging.error("layer directory already exists: %s", args.layer)
        sys.exit(1)
    cmd = ['git', 'diff', '--cached', '--shortstat']
    staged_changes = subprocess.check_output(cmd)
    if staged_changes:
        logging.error("index is not clean: %s"%(staged_changes))
        sys.exit(1)
    cmd = ['git', 'status', '--porcelain']
    unstaged_changes = {}
    for line in subprocess.check_output(cmd).split('\n'):
        if not line:
            continue
        assert line[2] == ' '
        status = line[:2]
        filename = line[3:]
        if '->' in filename:
            p = filename.split('->')
            assert len(p) == 2
            filename = p[0]
        unstaged_changes[filename] = status
    if '.gitmodules' in unstaged_changes:
        logging.error(".gitmodules is changed")
        sys.exit(1)
    cmd = ['git', 'submodule', 'add']
    if args.branch:
        cmd += ['-b', args.branch]
    cmd += ['--', args.url, args.layer]
    logging.info("Cloning %s", args.url)
    sts = subprocess.call(cmd)
    if sts != 0:
        logging.error("adding submodule failed: %d", sts)
        sys.exit(1)
    if args.branch and args.branch != 'master':
        pushd(args.layer)
        cmd = ['git', 'show-ref', '--verify', '--quiet', 'refs/heads/master']
        sts = subprocess.call(cmd)
        if sts == 0:
            cmd = ['git', 'branch', '-d', 'master']
            sts = subprocess.call(cmd)
            if sts != 0:
                logging.error("could not delete master branch: %d", sts)
                sys.exit(1)
            cmd = ['git', 'branch', '-M', args.branch, 'master']
            sts = subprocess.call(cmd)
            if sts != 0:
                logging.error("could not rename %s branch: %d",
                              args.branch, sts)
                sys.exit(1)
        popd()
    if args.commit:
        pushd(args.layer)
        cmd = ['git', 'reset', '--hard', args.commit]
        sts = subprocess.call(cmd)
        if sts != 0:
            logging.error("reset to requested commit failed: %d", sts)
            sys.exit(1)
        popd()
        cmd = ['git', 'add', args.layer]
        sts = subprocess.call(cmd)
        if sts != 0:
            logging.error("adding %s to index failed: %d", args.layer, sts)
            sys.exit(1)
    with open('.gitmodules', 'r') as gitmodules_file:
        gitmodules_lines = gitmodules_file.readlines()
        assert args.url in gitmodules_lines[-1]
        gitmodules_lines[-1] = "\turl = ./%s\n"%(args.layer)
    with open('.gitmodules', 'w') as gitmodules_file:
        gitmodules_file.write(''.join(gitmodules_lines))
    cmd = ['git', 'add', '.gitmodules']
    sts = subprocess.call(cmd)
    if sts != 0:
        logging.error("adding .gitmodules to index failed: %d", sts)
        sys.exit(1)
    cmd = ['git', 'commit', '-m', "Add layer %s from %s"%(args.layer, args.url)]
    logging.info("Committing new layer to manifest")
    sts = subprocess.call(cmd)
    if sts != 0:
        logging.error("committing new layer failed: %d", sts)
        sys.exit(1)
