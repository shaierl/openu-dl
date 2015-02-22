#!/usr/bin/env python2
################################################################################
# Class to launch encoder process
################################################################################
import os
import re
import subprocess
import progressbar

class Mencoder(object):
    __PROG_RE = re.compile("\(\s{0,1}(\d+)\%\)")
    __MENCODER_PROCESS = "mencoder"
    __MENCODER = "%s -forceidx %%(dl_target)s -o %%(target)s -oac mp3lame -ovc copy -ofps 60" % __MENCODER_PROCESS
    __PBAR_WIDGETS = ['Encoding: ', progressbar.Percentage(), ' ', progressbar.Bar(),
                    ' ', progressbar.ETA()]

    def __init__(self, source, dest, delete=True, verbose=True):
        self._source = source
        self._dest = dest
        self._verbose = verbose
        self._del = delete
        self._cmd = self.__MENCODER % {"target": self._dest, "dl_target": self._source}
        self._pbar = progressbar.ProgressBar(widgets=self.__PBAR_WIDGETS, maxval=100)

    @staticmethod
    def check_assert():
        assert 0 == subprocess.call(["which", Mencoder.__MENCODER_PROCESS],\
                stderr=subprocess.STDOUT,\
                stdout=subprocess.PIPE),\
        "mencoder is not installed"

    def start(self):
        "Start the mencoder process"

        print "Fixing encoding... (%s => %s)" % (self._source, self._dest)
        # Verbosity of progress bar
        if self._verbose:
            self._pbar.start()

        # Start the process
        s = subprocess.Popen(self._cmd.split(" "), stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        try:
            # Process the output
            for line in s.stdout:
                # Get precentage from the line
                p = self.__PROG_RE.findall(line)
                if not self._verbose or len(p) == 0:
                    continue

                p = int(p[0])
                self._pbar.update(p)
        finally:
            s.kill()
            s.wait()

        assert 0 == s.returncode, "Mencoder failed"

        # Remove the temp file
        if self._del:
            print "Removing old file... (%s)" % self._source
            os.unlink(self._source)
