import oelite.fetch
import oelite.git
import os
import re
import warnings
import string
import sys

import bb.utils

class GitFetcher():

    SUPPORTED_SCHEMES = ("git")
    COMMIT_ID_RE = re.compile("([0-9a-f]{1,40})")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.GitFetcher"%(scheme))
        uri.fdepends.append("native:git")
        self.uri = uri
        try:
            protocol = uri.params["protocol"]
        except KeyError:
            protocol = "git"
        self.url = "%s://%s"%(protocol, uri.location)
        repo_name = protocol + "_" + \
            self.uri.location.rstrip("/").translate(string.maketrans("/", "_"))
        self.repo = os.path.join(uri.ingredients, uri.isubdir, 'git', repo_name)
        self.mirror_name = repo_name
        if self.mirror_name.endswith(".git"):
            self.mirror_name = self.mirror_name[:-4]
        self.commit = None
        self.tag = None
        self.branch = None
        if "commit" in uri.params:
            self.commit = uri.params["commit"]
            if not self.COMMIT_ID_RE.match(self.commit):
                raise oelite.fetch.InvalidURI(
                    self.uri, "invalid commit id %s"%(repr(self.commit)))
        if "tag" in uri.params:
            self.tag = uri.params["tag"]
            self.signature_name = "git://" + uri.location
            if protocol != "git":
                self.signature_name += ";protocol=" + protocol
            self.signature_name += ";tag=" + self.tag
        if "branch" in uri.params:
            self.branch = uri.params["branch"]
        i = bool(self.commit) + bool(self.tag) + bool(self.branch)
        if i == 0:
            self.branch = "HEAD"
        elif i != 1:
            raise oelite.fetch.InvalidURI(
                self.uri, "cannot mix commit, tag and branch parameters")
        if "track" in uri.params:
            self.track = uri.params["track"].split(",")
            warnings.warn("track parameter not implemented yet")
        else:
            self.track = None
        repo_name = uri.location.strip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        if "subdir" in uri.params:
            self.dest = uri.params["subdir"]
            if self.dest[-1] == "/":
                self.dest += repo_name
        else:
            self.dest = repo_name
        self.signatures = d.get("FILE") + ".sig"
        self.fetch_signatures = d["__fetch_signatures"]
        return

    def signature(self):
        if self.commit:
            return self.commit
        elif self.tag:
            try:
                self._signature = self.fetch_signatures[self.signature_name]
                return self._signature
            except KeyError:
                raise oelite.fetch.NoSignature(self.uri, "signature unknown")
        elif self.branch:
            warnings.warn("fetching git branch head, causing source signature to not be sufficient for proper signature handling (%s)"%(self.uri))
            return ""
        raise Exception("this should not be reached")

    def fetch(self):
        # TODO: add special handling of file:// git repos, which should not
        # be cloned/mirrored to ingredients
        if not os.path.exists(self.repo):
            if not self.fetch_clone():
                return False
        repo = oelite.git.GitRepository(self.repo)
        if not self.has_rev(repo):
            if not self.fetch_update(repo):
                return False
        if self.tag:
            commit = repo.get_tag(self.tag)
            if not commit:
                raise oelite.fetch.FetchError(
                    self.uri, "unknown tag: %s"%(self.tag))
            if not "_signature" in dir(self):
                return (self.signature_name, commit)
            if (commit != self._signature):
                print "Error signature mismatch "+self.tag
                print "  expected: %s"%self._signature
                print "  obtained: %s"%commit
            return commit == self._signature
        return True

    def fetch_clone(self):
        basedir = os.path.dirname(self.repo)
        repodir = os.path.basename(self.repo)
        bb.utils.mkdirhier(basedir)
        options = ['--mirror']
        if self.uri.params.get('recursive', '0') != '0':
            options.append('--recursive')
        fetched = False
        for url in self.uri.premirrors + [self.url] + self.uri.mirrors:
            if not isinstance(url, basestring):
                if url[0].endswith("//"):
                    url = os.path.join(url[0].rstrip("/"), self.mirror_name)
                    url += ".git"
                else:
                    url = os.path.join(url[0], url[1])
            if not self.uri.allow_url(url):
                print "Skipping", url
                continue
            cmd = ['git', 'clone'] + options + [ url, repodir ]
            print "Cloning from", url
            if oelite.util.shcmd(cmd, dir=basedir) is True:
                return True
            print "fetching from %s failed"%(url)
        print "Error: git clone failed"
        return False

    def fetch_update(self, repo):
        fetched = False
        for url in self.uri.premirrors + [self.url] + self.uri.mirrors:
            if not isinstance(url, basestring):
                if url[0].endswith("//"):
                    url = os.path.join(url[0].rstrip("/"), self.mirror_name)
                    url += ".git"
                else:
                    url = os.path.join(url[0], url[1])
            if not self.uri.allow_url(url):
                print "Skipping", url
                continue
            print "Updating from %s"%(url)
            repo.remote_update(url)
            if self.has_rev(repo):
                return True
        print "Error: git update failed"
        return False

    def has_rev(self, repo):
        if self.commit:
            return repo.has_commit(self.commit)
        elif self.tag:
            return repo.has_tag(self.tag)
        elif self.branch:
            return repo.has_head(self.branch)
        return False

    def unpack(self, d):
        wc = os.path.join(d.get("SRCDIR"), self.dest)
        basedir = os.path.dirname(wc)
        bb.utils.mkdirhier(basedir)
        if self.branch:
            branch = self.resolve_head(self.branch)
            cmd = "git clone --shared -b %s %s %s"%(branch, self.repo, wc)
            if not oelite.util.shcmd(cmd):
                print "Error: git clone failed"
                return False
            return True
        cmd = "git clone --shared --no-checkout %s %s"%(self.repo, wc)
        if not oelite.util.shcmd(cmd):
            print "Error: git clone failed"
            return False
        cmd = "git checkout -q "
        if self.commit:
            cmd += self.commit
        elif self.tag:
            cmd += "refs/tags/%s"%(self.tag)
        else:
            print "Error: WTF! no commit, tag or branch!!"
            return False
        if not oelite.util.shcmd(cmd, dir=self.dest):
            print "Error: git checkout failed"
            return False
        return True

    def mirror(self, mirror=os.getcwd()):
        path = os.path.join(self.uri.isubdir, "git", self.mirror_name) + ".git"
        basedir = os.path.dirname(path)
        if not os.path.exists(path):
            print "Creating git mirror", path
            bb.utils.mkdirhier(basedir)
            options = ['--mirror']
            if self.uri.params.get('recursive', '0') != '0':
                options.append('--recursive')
            cmd = ['git', 'clone'] + options + [self.repo, path]
            return oelite.util.shcmd(cmd) is True
        else:
            print "Updating git mirror", path
            cmd = "git remote update"
            return oelite.util.shcmd(cmd, dir=path) is True
