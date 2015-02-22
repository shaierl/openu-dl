#!/usr/bin/env python2
################################################################################
# This script will login to OpenU to pull a video from it.
##
# Requirments:
# Python2 >= 2.7
# libmimms2 (https://github.com/itayperl/mimms2)
#   (note the library requirments)
# mencoder installed.
################################################################################

import sys
import os

from Downloader import Downloader
from OpenUCrawler import OpenUCrawler
from Mencoder import Mencoder

# TODO: Param with get-opts.
MAX_TRIES = 3

def download_all(threads, videos):
    print "Downloading with %s threads" % threads
    for fname, mms_url in videos:
        # TODO: Remove this after file selection menu.
        if os.path.isfile(fname):
            continue

        print "Processing %s" % fname

        # Downloading the file
        d = Downloader(mms_url, fname, threads, MAX_TRIES)
        d.start()

        # Now converting to the right format:
        mencoder = Mencoder(d.filename, d.target)
        mencoder.start()

    return 0

def main():
    ## TODO: Get opts library
    if len(sys.argv) != 7:
        print "Usage: %s <threads> <openu-user> <openu-password> <openu-id (T.Z)> <openu-semester> <openu-course>" % sys.argv[0]
        print "Example: %s 30 uberuser Pass123 123456789 2015a 20301" % sys.argv[0]
        return -1

    _, threads, user, password, iden, semester, course = sys.argv

    # Makes sure mencoder is installed.
    Mencoder.check_assert()

    # Search Videos
    craweler = OpenUCrawler(user, password, iden)
    videos = craweler.get_videos(semester, course)

    ## TODO: Menu to Filter videos

    # Read the MMS Out of the relevant vidoes
    videos = craweler.videos_to_mms(videos)

    ## TODO: Do it with a Queue?
    # Download one by one
    return download_all(threads, videos)

if __name__ == "__main__":
    main()
