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

import cookielib
import urllib
import urllib2
import sys
import re
import os
from libmimms2 import core as mimms2

# TODO: Param with get-opts.
MAX_TRIES = 3

class OpenUCrawler(object):
    __MMS_RE = re.compile("(mms://.+)'")
    __SEMESTER_RE = re.compile("^(\d{4}[abc])$")
    __COURSE_OPT_RE = re.compile("<option value='(http://.+?)'>.+?\((\d+?)\)</option>")
    __VIDEOS_LINK_RE = re.compile("href=\"(http:\/\/opal\.openu\.ac\.il\/mod\/ouvideo\/view\.php\?id=\d+)\"")
    __VIDEOS_RE_BASE = "href=\"(\/video\/redirect.php\?v=%(semester)s/.+?\.asx&c=c%(course)s)\""
    __UNAUTH_STR = "<form action=\"http://opal.openu.ac.il/index.php\" method=\"get\">"
    __UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36"
    __REDIRECT_URL = "http://opal.openu.ac.il/auth/ouilsso/redirect2.php?urltogo="
    __LOGIN_PAGE = "https://sso.apps.openu.ac.il/login?T_PLACE=%s" % __REDIRECT_URL
    __LOGIN_FORM = "https://sso.apps.openu.ac.il/process"
    __COURSE_SEARCH = "http://opal.openu.ac.il/blocks/ouil_course_suggestion/course_suggestion_ajax.php??build=1419488219&semester=%(semester)s" 
    __VIDEOS_PAGE_EXT = "%(base)s&perpage=100"
    __VIDEO_PLAYER_URL_BASE = "http://opal.openu.ac.il%(link)s"
    __FILE_NAMING_CONV = "%(semester)s_%(course)s_%(id)03d.wmv"

    def __init__(self, user, password, iden):
        self.__login(user, password, iden)

    def __login(self, user, password, iden):
        """
            Initial login to start the crawling
        """

        # Create CookieJar
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders.append(('User-agent', self.__UA))

        # Install it.
        urllib2.install_opener(opener)

        # Fill up form data
        data = urllib.urlencode({"p_user": user, 
            "p_sisma": password, 
            "p_mis_student": iden, 
            "T_PLACE": self.__REDIRECT_URL})

        # First open the login page to get a dummy cookie
        self.__read_page(self.__LOGIN_PAGE)

        # Next Do the login itself
        req = urllib2.Request(self.__LOGIN_FORM, data)
        resp = urllib2.urlopen(req).read()
        assert "alert" not in resp, "Wrong Username/Password/ID (T.Z) Provided"

    def __get_courses(self, semester):
        """
            return a dict of "course_id": "course_url"
        """

        assert 1 == len(self.__SEMESTER_RE.findall(semester)), "Semester needs to be a year + a/b/c"
        print "Read courses for %s" % semester
        raw = self.__read_page(self.__COURSE_SEARCH % {'semester': semester})
        return dict([(i[1], i[0]) for i in self.__COURSE_OPT_RE.findall(raw)])

    def __get_course_page(self, semster, course):
        """
            returns the course page content
        """

        # Get's all courses for target semster
        courses = self.__get_courses(semster)
        assert courses.has_key(course), "Course %s was not found." % course

        # Reading the course page content
        print "Read course page of course %s" % course
        cpage = self.__read_page(courses[course])
        assert self.__UNAUTH_STR not in cpage, "Unauthorized course for your user."

        # Return course page content
        return cpage

    def __get_video_page_url(self, semster, course):
        """
            returns the video page in the course page
        """

        # Gets course page content
        cpage = self.__get_course_page(semster, course)

        # Search for the video's link in the page
        video_links = self.__VIDEOS_LINK_RE.findall(cpage)
        assert len(video_links) != 0, "No videos in this course"
        vlink = video_links[0]
        print "Found course videos at %s" % vlink

        # Return the video page with extra params to eliminate pages
        return self.__VIDEOS_PAGE_EXT % {'base': vlink}

    def __read_page(self, url):
        """ Reads target url """
        return urllib2.urlopen(urllib2.Request(url)).read()

    def player_url_to_mms(self, player_url):
        """
            Opens the player page to retrieve an mms url
        """
        # Reads the player page content
        resp = self.__read_page("%s&fallback=1" % player_url)
        assert "mms://" in resp, "Invalid page provided"

        # Search for the mms prefix in it.
        return self.__MMS_RE.findall(resp)[0]

    def get_videos(self, semester, course):
        """
            Returns a dict of "filename": "player_url"
            for all videos in the course in the semester
        """
        # Builds the video page RE depends on course and semester
        videos_re = re.compile(self.__VIDEOS_RE_BASE % {'semester': semester, 'course': course})

        # Find the video's page URL
        videos_url = self.__get_video_page_url(semester, course)

        # Find all video player links in the page
        all_videos = videos_re.findall(self.__read_page(videos_url))
        assert len(all_videos) != 0, "No videos in this course"

        # Format the urls with a filename
        formatted = [(self.__FILE_NAMING_CONV % {'semester': semester, 'course': course, 'id': i+1}, 
            self.__VIDEO_PLAYER_URL_BASE % {'link': url}) for i, url in enumerate(all_videos)]
        return dict(formatted)

    def videos_to_mms(self, videos):
        """
            retrive a filtered videos dict (see get_videos)
            and convert all player_urls to mms_urls

            The function will return a sorted list of (fname, url)
        """

        mms = []
        for fname, player_url in videos.iteritems():
            mms.append((fname, self.player_url_to_mms(player_url)))
        mms.sort(key=lambda x: x[0])
        return mms

class Downloader(object):
    def __init__(self, mms_url, filename, threads=10):
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
                print "Failed, to download (%d out of %d)" % (tries, MAX_TRIES)
                os.unlink(self._filename)
                if tries >= MAX_TRIES:
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

class Mencoder(object):
    __MENCODER = "mencoder -forceidx %(dl_target)s -o %(target)s -oac mp3lame -ovc copy -ofps 60"

    def __init__(self, source, dest, delete=True):
        self._source = source
        self._dest = dest
        self._del = delete
        self._cmd = self.__MENCODER % {"target": self._dest, "dl_target": self._source}

    def start(self):
        print "Fixing encoding... (%s => %s)" % (self._source, self._dest)
        # TODO: Change to Subprocess, to Eliminate prints wisely.
        os.system("%s &> /dev/null" % (self._cmd))

        # Remove the temp file
        if self._del:
            print "Removing old file... (%s)" % self._source
            os.unlink(self._source)

def download_all(threads, videos):
    print "Downloading with %s threads" % threads
    for fname, mms_url in videos:
        # TODO: Remove this after file selection menu.
        if os.path.isfile(fname):
            continue

        print "Processing %s" % fname

        # Downloading the file
        d = Downloader(mms_url, fname, threads)
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
