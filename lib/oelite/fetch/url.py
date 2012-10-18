import oelite.fetch
import bb.utils
import os
import urlgrabber
import urlgrabber.progress
import hashlib

class UrlFetcher():

    SUPPORTED_SCHEMES = ("http", "https", "ftp")

    def __init__(self, uri, d):
        if not uri.scheme in self.SUPPORTED_SCHEMES:
            raise Exception(
                "Scheme %s not supported by oelite.fetch.UrlFetcher"%(
                    uri.scheme))
        self.url = "%s://%s"%(uri.scheme, uri.location)
        self.localname = os.path.basename(uri.location)
        self.localpath = os.path.join(uri.ingredients, uri.isubdir,
                                      self.localname)
        self.signatures = d.get("FILE") + ".sig"
        self.uri = uri
        self.fetch_signatures = d["__fetch_signatures"]
        return

    def signature(self):
        try:
            self._signature = self.fetch_signatures[self.localname]
            return self._signature
        except KeyError:
            raise oelite.fetch.NoSignature(self.uri, "signature unknown")

    def fetch(self):
        localdir = os.path.dirname(self.localpath)
        if not os.path.exists(localdir):
            bb.utils.mkdirhier(localdir)

        if os.path.exists(self.localpath):
            if "_signature" in dir(self):
                signature = self.localsignature()
                if signature == self._signature:
                    return True
            print "Removing unverifiable ingredient:", \
                os.path.join(self.uri.isubdir, self.localname)
            os.unlink(self.localpath)

        grabbed = False
        for url in self.uri.premirrors + [self.url] + self.uri.mirrors:
            assert not os.path.exists(self.localpath)
            if not isinstance(url, basestring):
                url = "".join(url)
            if not self.uri.allow_url(url):
                print "Skipping", url
                continue
            if grab(url, self.localpath):
                grabbed = True
                break
            if os.path.exists(self.localpath):
                print "Removing ingredient littering:", \
                    os.path.join(self.uri.isubdir, self.localname)
                os.unlink(self.localpath)
        if not grabbed:
            return False
        assert os.path.exists(self.localpath)

        signature = self.localsignature()
        if not "_signature" in dir(self):
            return (self.localname, signature)
        if signature != self._signature:
            print "Ingredient signature mismatch:", \
                os.path.join(self.uri.isubdir, self.localname)
            print "  expected: %s"%self._signature
            print "  obtained: %s"%signature
            return False
        else:
            return True

    def localsignature(self):
        m = hashlib.sha1()
        m.update(open(self.localpath, "r").read())
        return m.hexdigest()


class SimpleProgress(urlgrabber.progress.BaseMeter):
    def _do_end(self, amount_read, now=None):
        print "grabbed %d bytes in %.2f seconds" %(amount_read,self.re.elapsed_time())


def grab(url, filename, timeout=120, retry=5):
    print "Grabbing", url
    def grab_fail_callback(data):
        # Only print debug here when non fatal retries, debug in other cases
        # is already printed
        if (data.exception.errno in retrycodes) and (data.tries != data.retry):
            print "grabbing retry %d/%d, exception %s"%(
                data.tries, data.retry, data.exception)
    try:
        retrycodes = urlgrabber.grabber.URLGrabberOptions().retrycodes
        if 12 not in retrycodes:
            retrycodes.append(12)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        downloaded_file = urlgrabber.urlgrab(
            url, filename,timeout=timeout,retry=retry, retrycodes=retrycodes,
            progress_obj=SimpleProgress(), failure_callback=grab_fail_callback,
            copy_local=True)
        if not downloaded_file:
            return False
    except urlgrabber.grabber.URLGrabError as e:
        print 'URLGrabError %i: %s' % (e.errno, e.strerror)
        if os.path.exists(filename):
            os.unlink(filename)
        return False
    return True
