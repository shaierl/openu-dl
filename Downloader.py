#!/usr/bin/env python2
################################################################################
# Downloader class (uses mimms2)
################################################################################

# Hack to import from submodule:
import os
import sys
__ORG_PATH = sys.path[:]
__CUR_DIR = os.path.split(__file__)[0]
sys.path.append(os.path.join(__CUR_DIR, "mimms2"))
from libmimms2 import core as mimms2
sys.path = __ORG_PATH

class Downloader(object):
    def __init__(self, mms_url, filename, threads=10, retries=3):
        self._retries = retries
        self._threads = int(threads)
        self._bw = 1e6
        self._verbose = True
        self._target = filename
        self._filename = "%s_tmp" % self._target
        self._clobber = False
        self._mms_url = mms_url

        self._filename = mimms2.get_filename(self)

    def start(self):
        tries = 0

        print "Downloading url %s" % self._mms_url
        print "Downloading to %s" % self._filename

        while True:
            try:
                return mimms2.download_threaded(self._mms_url, self._bw, self._filename, conn_count=self._threads, verbose=self._verbose)
            except AssertionError, e:
                tries += 1
                print "Failed, to download (%d out of %d)" % (tries, self._retries)
                os.unlink(self._filename)
                if tries >= self._retries:
                    raise
        return True

    @property
    def filename(self):
        return self._filename

    @property
    def clobber(self):
        return self._clobber

    @property
    def target(self):
        return self._target
