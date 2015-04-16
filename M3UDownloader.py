#!/usr/bin/env python2
################################################################################
# M3UDownloader will download target m3u + referred files into
# target directory
################################################################################

from DownloaderThread import DownloaderThread
import progressbar
import shutil
import os
from urlparse import urljoin

class M3UDownloader(object):
    __PBAR_WIDGETS = ['Downloading: ', progressbar.Percentage(), ' ', progressbar.Bar(),
                    ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]

    __PBAR_PREPARE_WIDGETS = ['Preparing: ', progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]

    def __init__(self, target_url, target_dir, threads=15, verbose=True):
        self.__target_dir = os.path.realpath(target_dir)
        self.__target_url = target_url
        self.__index_file = os.path.join(self.__target_dir, "index.m3u8")
        self.__targets = []
        self.__total_size = 0
        self.__verbose = verbose
        self.__max_threads = threads

        # Prepare empty directory
        self.__prepare_directory()

        # Download index file into it
        self.__download_index()

        # Prepare targets list
        self.__prepare_targets()

    def start(self):
        self.__download()
        self.__assert_files()

    @property
    def target_dir(self):
        return self.__target_dir

    @property
    def index_file(self):
        return self.__index_file

    def __assert_files(self):
        for t in self.__targets:
            assert os.path.isfile(t.target_file), "File %s was not downloaded" % t.target_file

    def __download(self):
        # Do we have a job here?
        if 0 == len(self.__targets):
            return

        left_threads = self.__targets[:]
        active_threads = []
        pbar = progressbar.ProgressBar(widgets=self.__PBAR_WIDGETS, maxval=self.__total_size)

        # Start progress bar
        if self.__verbose:
            print "Downloading to %s" % (self.__target_dir)
            pbar.start()

        # Start iterate all threads till done.
        while len(left_threads) > 0 or len(active_threads) > 0:
            # First activate all threads
            while len(left_threads) > 0 and len(active_threads) < self.__max_threads:
                t = left_threads.pop()
                t.start()
                active_threads.append(t)

            # Update progress bar
            if self.__verbose:
                pbar.update(self.__total_downloaded())

            # Handling exceptions:
            for t in active_threads:
                if t.exception:
                    raise t.exception

            # Remove finished threads
            active_threads = filter(lambda x: x.is_running, active_threads)

    def __total_presentage(self):
        return sum([i.presentage for i in self.__targets])

    def __total_downloaded(self):
        return sum([i.downloaded for i in self.__targets])

    def __prepare_directory(self):
        """ Makes sure we will start with empty directory """
        if os.path.isdir(self.__target_dir):
            #shutil.rmtree(self.__target_dir)
            return

        os.mkdir(self.__target_dir)

    def __prepare_targets(self):
        with file(self.__index_file, "r") as f:
            lines = [i.strip() for i in f.readlines()]

        assert lines[0].startswith("#EXTM3U"), "Invalid M3U File Downloaded"

        for line in lines[1:]:
            if line.startswith("#"): # Info line
                continue

            # Line contain filename
            url = urljoin(self.__target_url, line)
            target_file = os.path.join(self.__target_dir, line)

            # Append to targets
            self.__targets.append(DownloaderThread(url, target_file))

        # Preparing All targets
        pbar = progressbar.ProgressBar(widgets=self.__PBAR_PREPARE_WIDGETS, maxval=len(self.__targets))
        if self.__verbose:
            print "Preparing to Download %s" % (self.__target_url)
            pbar.start()

        total_size = 0
        for i, t in enumerate(self.__targets):
            pbar.update(i+1)
            t.prepare()
            total_size += t.total_size

        self.__total_size = total_size

    def __download_index(self):
        # Start a downloader thread for the index and wait until done
        d = DownloaderThread(self.__target_url, self.__index_file)
        d.prepare()
        d.start()
        d.join()
        if d.exception:
            raise d.exception
