#!/usr/bin/env python2
################################################################################
# DownloaderThread is one thread for download system
################################################################################

import threading
import urllib2
import socket

class DownloaderThread(threading.Thread):
    def __init__(self, target_url, target_file, chunk_size=8192, max_retries=5, timeout=5):
        # Init download variables
        self.__target_url = target_url
        self.__target_file = target_file
        self.__chunk_size = chunk_size
        self.__max_retries = max_retries
        self.__timeout = 5
        self.__presentage = 0
        self.__running = True
        self.__started = False

        # Init Thread
        super(DownloaderThread, self).__init__()
        self.daemon = True

        # Wrap run for exceptions
        self.__exception = None
        self.__real_run = self.run
        self.run = self.__run_wrapper

    def run(self):
        """ Main of the thread """
        if not self.__running:
            return

        self.__started = True
        self.__download_with_retries()
        self.__running = False

    def kill(self):
        """ Signal the thread to stop working and wait until done """
        if not self.__running or not self.isAlive():
            return

        self.__running = False
        self.join()

    @property
    def is_running(self):
        if not self.__started:
            return True

        return self.isAlive()

    @property
    def target_file(self):
        return self.__target_file

    @property
    def presentage(self):
        return self.__presentage

    @property
    def exception(self):
        return self.__exception

    def __run_wrapper(self, **kargs):
        try:
            return self.__real_run(**kargs)
        except Exception, e:
            self.__exception = e
            self.__running = False

    def __download_with_retries(self):
        """ Download with retry loop """

        tries = 0
        while True:
            try:
                tries += 1
                return self.__download_file()
            except (socket.timeout, urllib2.HTTPError) as e:
                if tries <= self.__max_retries:
                    continue
                raise

    def __download_file(self):
        """ Download operation """

        # Open a request
        resp = urllib2.urlopen(url=self.__target_url, timeout=self.__timeout)

        # Open the file for writing and invoke read_chunks.
        with file(self.__target_file, "wb") as f:
            self.__read_chunks(resp, f)

    def __read_chunks(self, resp, f):
        """
            This file will download all resp content
            into f file object
        """

        total_dl = 0
        total_size = int(resp.info().getheader('Content-Length').strip())

        while self.__running and self.__presentage != 100:
            # Read the chunk
            chunk = resp.read(self.__chunk_size)
            if not chunk:
                break

            # Write to file
            f.write(chunk)

            # Calc the presentage
            total_dl += len(chunk)
            self.__presentage = (total_dl * 100) / total_size
