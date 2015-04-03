#!/usr/bin/env python2
################################################################################
# This script will login to OpenU to pull a video from it.
##
# Requirments:
#   python >= 2.7 (python3 is not supported)
#   python-progressbar - <https://pypi.python.org/pypi/progressbar/2.3-dev>
#   ffmpeg - <https://help.ubuntu.com/community/FFmpeg>
################################################################################

import sys
import os
import shutil

from OpenUCrawler import OpenUCrawler
from FFMpeg import FFMpeg
from M3UDownloader import M3UDownloader

def download_all(videos):
    for fname, video_url in videos:
        # TODO: Remove this after file selection menu.
        if os.path.isfile(fname):
            continue

        print "Processing %s" % fname

        # Downloading the files
        m = M3UDownloader(video_url, "%s_files" % fname)
        m.start()

        # Encode to one container
        d = FFMpeg(m.index_file, fname)
        d.start()

        # Remove left overs
        shutil.rmtree(m.target_dir)

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
