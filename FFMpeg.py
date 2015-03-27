#!/usr/bin/env python2
################################################################################
# Class to launch downloader/encoder process
################################################################################
import os
import re
import subprocess
import progressbar
import fcntl
import select
from datetime import datetime
from time import mktime

class FFMpeg(object):
    __DURATION_RE = re.compile("Duration:\s(.+?),")
    __PROG_RE = re.compile("time=(.+?)\s")
    __FFMPEG_PROCESS = "ffmpeg"
    __FFMPEG = '%s -i %%(dl_target)s -c copy %%(target)s'  % __FFMPEG_PROCESS
    __PBAR_WIDGETS = ['Downloading: ', progressbar.Percentage(), ' ', progressbar.Bar(),
                    ' ', progressbar.ETA()]

    def __init__(self, source, dest, verbose=True):
        self._source = source
        self._dest = dest
        self._verbose = verbose
        self._pbar_maxval = 10000
        self._cmd = self.__FFMPEG % {"target": self._dest, "dl_target": self._source}
        self._pbar = progressbar.ProgressBar(widgets=self.__PBAR_WIDGETS, maxval=self._pbar_maxval)

    @staticmethod
    def check_assert():
        assert 0 == subprocess.call(["which", FFMpeg.__FFMPEG_PROCESS],\
                stderr=subprocess.STDOUT,\
                stdout=subprocess.PIPE),\
        "FFMpeg is not installed"

    def __duration_to_ts(self, duration):
        " Convert duration string to timestamp "
        # Parse to time object
        d = datetime.strptime(duration, "%H:%M:%S.%f").time()

        # Calc total seconds
        total = 0
        total += d.second
        total += d.minute * 60
        total += d.hour * 60 * 60
        return total


    def start(self):
        "Start the FFMpeg process"

        print "Downloading and converting... (%s => %s)" % (self._source, self._dest)

        # Verbosity of progress bar
        if self._verbose:
            self._pbar.start()

        # Start the process
        s = subprocess.Popen(self._cmd.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        # Set stderr non-blocking
        fcntl.fcntl(s.stderr.fileno(), fcntl.F_SETFL,
                fcntl.fcntl(s.stderr.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)

        duration = None
        try:
            # Process the output
            while True:
                # Select on stderr to determinate output is avliable
                readx = select.select([s.stderr.fileno()], [], [])[0]
                if not readx:
                    continue

                # Reads current line (None is EOF)
                line = s.stderr.read()
                if not line:
                    break # EOF Reached.

                # Phase 1: read duration of the video
                if duration is None:
                    d = self.__DURATION_RE.findall(line)
                    if len(d) == 0:
                        continue
                    duration = self.__duration_to_ts(d[0])

                # Phase 2: Encoding started, Get current duration from the line
                p = self.__PROG_RE.findall(line)
                if not self._verbose or len(p) == 0:
                    continue

                # Convert to timestamp
                p = self.__duration_to_ts(p[0])

                # Finally, update progress (Relative to duration)
                self._pbar.update((p * self._pbar_maxval / duration))
        finally:
            s.kill()
            s.wait()

        assert 0 == s.returncode, "FFMpeg failed"
