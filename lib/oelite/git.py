import os
import re
import string
import sys
import logging

import oelite.util
import bb.utils


class NotAGitRepository(Exception):
    def __init__(self, path):
        self.path = path
    def __str__(self):
        print self.path


class GitRepository(object):

    SHA1_RE = re.compile("([0-9a-f]{1,40})$")

    def __init__(self, path):
        self.path = oelite.util.shcmd(
            "git rev-parse --show-toplevel", dir=path,
            quiet=True, silent_errorcodes=[128])
        if self.path is None:
            raise NotAGitRepository(path)
        elif self.path == '':
            # assuming that path is top-level of a bare repository
            self.path = path
        self.path = self.path.strip()

    def git(self, cmd, quiet=True, strip=True):
        if not isinstance(cmd, basestring):
            cmd = " ".join(cmd)
        cmd = "git " + cmd
        retval = oelite.util.shcmd(
            cmd, dir=self.path, quiet=quiet, silent_errorcodes=[1, 128])
        if not quiet:
            return retval
        if strip and retval:
            retval = retval.strip()
        return retval

    def has_head(self, head):
        return self.resolve_head(head) is not None

    def resolve_head(self, ref):
        if self.has_ref(ref, 'heads'):
            return ref
        # dereference symbolic references (such as HEAD)
        head = self.get_symref(ref)
        if head is None:
            return None
        if not head.startswith("refs/heads/"):
            logging.warning("ignoring non-head symbolic reference: %s", head)
            return None
        head = head[11:]
        if self.has_ref(head, 'heads'):
            return head
        return None

    def heads(self):
        heads = self.git(
            "for-each-ref refs/heads/ --format '%(refname:short)'")
        if not heads:
            return None
        return heads.split("\n")

    def has_tag(self, tag):
        return self.has_ref(tag, 'tags')

    def has_ref(self, ref, type):
        assert type in ('heads', 'tags')
        if not ref.startswith("refs/%s/"%(type)):
            ref = "refs/%s/%s"%(type, ref)
        return self.git("show-ref -q --verify --%s %s"%(type, ref)) is not None

    def get_head(self, head):
        return self.get_rev(head, 'heads')

    def get_tag(self, head):
        # FIXME: get the sha1 of the commit object, not the tag object.
        return self.get_rev(head, 'tags')

    def get_rev(self, rev, type):
        assert type in ('heads', 'tags')
        if not rev.startswith("refs/%s/"%(type)):
            rev = "refs/%s/%s"%(type, rev)
        if type == 'tags':
           rev = '%s^{commit}'%(rev)
        commit = self.git("rev-parse --verify %s"%(rev))
        if commit is None:
            return None
        m = self.SHA1_RE.match(commit)
        if m is None:
            print "Warning: unexpected rev-parse output: %r"%(commit)
            return None
        return m.group(0)

    def get_symref(self, symref):
        head = self.git("symbolic-ref %s"%(symref))
        if not head:
            return None
        return head

    def has_commit(self, commit):
        if not self.SHA1_RE.match(commit):
            return False
        t = self.git("cat-file -t %s"%(commit))
        return t == 'commit'

    def set_url(self, url):
        return self.git("remote set-url origin %s"%(url))

    def remote_update(self, url=None):
        if url is not None:
            oldurl = self.git("config --get remote.origin.url")
            assert oldurl
            if url != oldurl:
                self.set_url(url)
        try:
            return self.git("remote update", quiet=False) is True
        finally:
            if url and url != oldurl:
                self.set_url(oldurl)

    def get_object(self, rev):
        return GitObject(self, rev)

    def get_dirt(self):
        untracked = self.git("ls-files --other --exclude-standard")
        untracked = ' '.join(untracked.split())
        if untracked:
            self.git("add %s"%(untracked))
        diff = self.git("diff HEAD", strip=False)
        if untracked:
            self.git("rm --cached %s"%(untracked))
        return diff


class GitObject(object):

    def __init__(self, repo, rev):
        content = repo.git("cat-file -p %s"%(rev))
        self.fields = {}
        lines = map(string.strip, content.splitlines())
        for line in xrange(len(lines)):
            if not lines[line]:
                break
            name, value = lines[line].split(' ', 1)
            if not hasattr(self, name):
                setattr(self, name, value)
            elif isinstance(getattr(self, name), basestring):
                setattr(self, name, [getattr(self, name), value])
            else:
                getattr(self, name).append(value)
        line += 1
        self.subject = lines[line]
        line += 1
        if line >= len(lines):
            self.body = None
            return
        self.body = '\n'.join(lines[line:])
