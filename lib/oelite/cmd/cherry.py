import oebakery
import logging
import oelite.util
import oelite.git


description = "Cherry pick tool"
arguments = (
    ("upstream", "Upstream branch to look for cherry pick candidates in", 0),
    ("head", "Release branch to consider cherry picking to (default is current branch)", 1))


def add_parser_options(parser):
    parser.add_option("-i", "--interactive",
                      action="store_true", default=False,
                      help="Interactive mode, allows setting target version for candidate commits")
    parser.add_option("-r", "--repository",
                      action="store", default=None,
                      help="Git repository (default is current directory)")
    parser.add_option("-d", "--debug",
                      action="store_true", default=False,
                      help="Debug the OE-lite metadata")
    return


def parse_args(options, args):
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    if options.interactive and not os.isatty(sys.stdin.fileno()):
        options.interactive = False
    if len(args) < 1 or len(args) > 2:
        return "bad argument count: %d (3 required)"%(len(args))
    options.upstream = args.pop(0)
    if args:
        options.head = args.pop(0)
    else:
        options.head = None
    return


# most the actual code below this point should probably go in a seperate file
# to prepare for reuse in other commands

import sys
import os
import copy
import re


class InvalidGitLogLine:
    pass


class RefLogIterator():

    def __init__(self, reflog, reverse=False):
        self.__reflog = reflog
        self.__list = reflog.list()
        if reverse:
            self.__list.reverse()
        return

    def __iter__(self):
        return self

    def next(self):
        if not self.__list:
            raise StopIteration()
        return self.__reflog[self.__list.pop()]


class RefLog:

    def __init__(self, repo, since=None, until=None):
        self.repo = repo
        self.__commits = {}
        if not since:
            self.__reflog = []
            return
        assert until
        self.__reflog = self.__parse_git_log(
            repo.git("log %s..%s"%(since, until)))
        return

    def __copy__(self):
        newreflog = RefLog(self.repo)
        newreflog.__commits.update(self.__commits)
        newreflog.__reflog = copy.copy(self.__reflog)
        return newreflog

    def __len__(self):
        return len(self.__reflog)

    def __getitem__(self, key):
        return self.__commits[key]

    def __delitem__(self, key):
        self.__reflog.remove(key)
        return

    def __iter__(self):
        return RefLogIterator(self)

    def __reversed__(self):
        return RefLogIterator(self, reverse=True)

    def __contains__(self, item):
        return item in self.__reflog

    def list(self):
        return copy.copy(self.__reflog)

    def __parse_git_log(self, log):
        self.__log = log.splitlines()
        self.__next_line()
        reflog = []
        while self.__line is not None:
            commit = self.__get_commit_line()
            headers = {}
            while True:
                header = self.__get_header_line()
                if not header:
                    break
                headers[header[0]] = header[1]
            self.__get_empty_line()
            msg = self.__get_indented_lines()
            msg = "\n".join(msg)
            self.__get_empty_line()
            if self.__line == "Notes:":
                self.__next_line()
                notes = "\n".join(self.__get_indented_lines())
                self.__get_empty_line()
            else:
                notes = None
            reflog.append(commit)
            self.__commits[commit] = commit
        #reflog.reverse()
        del self.__log, self.__line
        return reflog

    def __next_line(self):
        try:
            self.__line = self.__log.pop(0)
        except IndexError:
            self.__line = None
        return

    __commit_re = re.compile(r"commit ([0-9a-f]{40})")
    def __get_commit_line(self):
        m = self.__commit_re.match(self.__line)
        if not m:
            logging.error("invalid git log commit line: %s", self.__line)
            raise InvalidGitLogLine()
        self.__next_line()
        return m.group(1)

    __header_re = re.compile(r"([A-Za-z]+): +(.*)")
    def __get_header_line(self):
        m = self.__header_re.match(self.__line)
        if not m:
            return None
        self.__next_line()
        return m.groups()

    def __get_empty_line(self):
        if self.__line is None:
            return
        if self.__line.strip():
            logging.error("invalid line after commit header: %s", self.__line)
            raise InvalidGitLogLine()
        self.__next_line()
        return

    def __get_indented_line(self):
        if not self.__line or not self.__line.startswith("    "):
            return None
        indented_line = self.__line[4:]
        self.__next_line()
        return indented_line

    def __get_indented_lines(self):
        lines = []
        indented_line = self.__get_indented_line()
        while indented_line is not None:
            lines.append(indented_line)
            indented_line = self.__get_indented_line()
        return lines

def is_head_detached(repo):
    cmd = "git symbolic-ref HEAD"
    return oelite.util.shcmd(cmd, dir=repo, quiet=True,
                             silent_errorcodes=[1, 128]) is None

def run(options, args, config):
    logging.debug("cherry.run %s", options)

    if options.repository:
        if not os.path.exist(options.repository):
            return "invalid submodule path: %s"%(options.repository)
        repo = oelite.git.GitRepository(options.repository)
    else:
        try:
            repo = oelite.git.GitRepository(oebakery.oldpwd)
        except oelite.git.NotAGitRepository:
            return "unable to determine repository path"
    logging.debug("repository %r", repo.path)

    if not options.head:
        head = repo.get_symref('HEAD')
        if head is None:
            return "cannot determined release branch"
        options.head = head

    if re.match(r"[0-9\.]+$", options.head) is None:
        return "not a release branch: %r"%(options.head)

    if not options.head in repo.heads():
        return "invalid branch to cherry pick to: %s"%(options.head)

    cherry_base = repo.git("merge-base %s %s"%(options.head, options.upstream))
    if not cherry_base:
        return "failed to determine cherry base"

    upstream_log = RefLog(repo, cherry_base, options.upstream)
    head_log = RefLog(repo, cherry_base, options.head)

    logging.debug("examining %d commits", len(upstream_log))

    candidates = copy.copy(upstream_log)

    logging.debug("removing already merged commits")
    cherry = repo.git("cherry %s %s"%(options.head, options.upstream))
    cherry_re = re.compile(r"(.) ([0-9a-f]{40})")
    for line in cherry.splitlines():
        m = cherry_re.match(line)
        if not m:
            return "bad git cherry line: %s"%(line)
        prefix, sha = m.groups()
        if prefix == "-":
            logging.debug("removing %s %s", sha, candidates[sha])
            del candidates[sha]

    logging.debug("commits left: %d", len(candidates))

    logging.debug("removing seemingly merged commits")
    cherry_pick_re = re.compile("cherry picked from commit ([0-9a-f]{40})")
    for ref in head_log:
        commit = repo.get_object(ref)
        if not commit.body:
            continue
        for sha in cherry_pick_re.findall(commit.body):
            if sha in candidates:
                logging.debug("removing %s %s", sha, candidates[sha])
                del candidates[sha]

    logging.debug("commits left: %d", len(candidates))

    # filter out candidates based on "Target version" notes
    #  if target_version > pick_to: remove
    logging.debug("removing commits based on target version notes")
    def vercmp(target_version, release_branch):
        assert isinstance(target_version, basestring)
        if target_version == "master":
            return False
        target_version = map(int, target_version.split("."))
        assert len(target_version) > 0 and len(target_version) < 3
        assert isinstance(release_branch, basestring)
        release_branch = map(int, release_branch.split("."))
        assert len(release_branch) == 2
        if target_version[0] != release_branch[0]:
            return False
        if len(target_version) == 1:
            return True
        if target_version[1] > release_branch[1]:
            return False
        return True
    for ref in candidates:
        notes = repo.git("notes show %s"%(ref))
        target_version_re = re.compile("Target version: (.*)")
        if not notes:
            target_version = None
        else:
            for line in notes.splitlines():
                m = target_version_re.match(line)
                if m:
                    target_version = m.group(1).strip()
                    break
        if options.interactive and not target_version:
            commit = repo.get_object(ref)
            print "\ncommit %s\n%s"%(ref, commit.subject)

            while not target_version:
                target_version = raw_input("Target version [? to show diff]: ")
                if target_version == '?':
                    print "\n%s\n"%(repo.git("show --color %s"%(ref), quiet=True))
                    target_version = None
                    continue
                elif target_version == "master":
                    break
                if not target_version:
                    target_version = None
                    break
                if re.match(r"[0-9\.]+$", target_version):
                    break
                logging.error("invalid target version input: %s",
                              target_version)
                target_version = None
            if target_version:
                repo.git("notes append -m 'Target version: %s' %s"%(
                        target_version, ref))
        if target_version:
            if not vercmp(target_version, options.head):
                logging.debug("removing %s [Target version: %s]",
                              ref, target_version)
                del candidates[ref]
        pass

    print "cherry pick candidates from %s to %s: %d (oldest last)"%(
        options.upstream, options.head, len(candidates))
    for ref in reversed(candidates):
        commit = repo.get_object(ref)
        print "%s %s"%(ref, commit.subject)

    return 0
