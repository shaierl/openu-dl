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

from OpenUCrawler import OpenUCrawler
from FFMpeg import FFMpeg

def download_all(videos):
    for fname, mms_url in videos:
        # TODO: Remove this after file selection menu.
        if os.path.isfile(fname):
            continue

        print "Processing %s" % fname
        # TODO: Write multi-threaded downloader,
        # First download all chunks to disc, then use FFMpeg to contain them
        # into one file.

        # Downloading the file
        d = FFMpeg(mms_url, fname)
        d.start()

    return 0

def main():
    ## TODO: Get opts library
    if len(sys.argv) != 6:
        print "Usage: %s <openu-user> <openu-password> <openu-id (T.Z)> <openu-semester> <openu-course>" % sys.argv[0]
        print "Example: %s 30 uberuser Pass123 123456789 2015a 20301" % sys.argv[0]
        return -1

    _, user, password, iden, semester, course = sys.argv

    # Makes sure mencoder is installed.
    FFMpeg.check_assert()

    # Search Videos
    craweler = OpenUCrawler(user, password, iden)
    classes = craweler.get_videos(semester, course)

    ## TODO: Menu to Filter videos

    # Read the MMS Out of the relevant vidoes
    videos = craweler.classes_to_media(classes)

    ## TODO: Do it with a Queue?
    # Download one by one
    return download_all(videos)

if __name__ == "__main__":
    main()
