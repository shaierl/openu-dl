#!/usr/bin/env python2
################################################################################
# Crawler for OpenU Website
################################################################################

import cookielib
import urllib
import urllib2
import re
from urlparse import urljoin

class OpenUCrawler(object):
    __MEDIA_RE = re.compile("location=\"(.+?)\";")
    __BANDWIDTH_RE = re.compile("(chunklist_b(\d+)\.m3u8)")
    __SEMESTER_RE = re.compile("^(\d{4}[abc])$")
    __COURSE_OPT_RE = re.compile("<option value='(http://.+?)'>.+?\((\d+?)\)</option>")
    __VIDEOS_LINK_RE = re.compile("href=\"(http:\/\/opal\.openu\.ac\.il\/mod\/ouvideo\/view\.php\?id=\d+)\"")
    __VIDEOS_RE_BASE = "href=\"(\/video\/redirect.php\?v=%(semester)s/.+?\.asx&c=c%(course)s)\""
    __UNAUTH_STR = "<form action=\"http://opal.openu.ac.il/index.php\" method=\"get\">"
    __UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"
    __REDIRECT_URL = "http://opal.openu.ac.il/auth/ouilsso/redirect2.php?urltogo="
    __LOGIN_PAGE = "https://sso.apps.openu.ac.il/login?T_PLACE=%s" % __REDIRECT_URL
    __LOGIN_FORM = "https://sso.apps.openu.ac.il/process"
    __COURSE_SEARCH = "http://opal.openu.ac.il/blocks/ouil_course_suggestion/course_suggestion_ajax.php??build=1419488219&semester=%(semester)s" 
    __VIDEOS_PAGE_EXT = "%(base)s&perpage=100"
    __VIDEO_PLAYER_URL_BASE = "http://opal.openu.ac.il%(link)s"
    __FILE_NAMING_CONV = "%(semester)s_%(course)s_%(id)03d.ts"

    def __init__(self, user, password, iden):
        self.__login(user, password, iden)

    def __login(self, user, password, iden):
        """
            Initial login to start the crawling
        """

        # Create CookieJar
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders.append(('User-Agent', self.__UA))

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
        req = urllib2.Request(url)
        req.add_unredirected_header('User-Agent', self.__UA)
        return urllib2.urlopen(req).read()

    def player_url_to_media(self, player_url):
        """
            Opens the player page to retrieve an video url
        """
        # Reads the player page content
        resp = self.__read_page(player_url)

        # Search for the video prefix in it.
        re_results = self.__MEDIA_RE.findall(resp)
        assert len(re_results) == 2, "Invalid page provided"

        # Reads the playlist and extract all possible resulotions
        playlist_url = re_results[0]
        m3u_content = self.__read_page(playlist_url)
        assert m3u_content.startswith("#EXTM3U"), "Invalid m3u8 file provided"

        # Extract all possible urls & bitrates from the playlist
        playlist_content = self.__BANDWIDTH_RE.findall(m3u_content)
        playlist_content = [(url, int(bitrate)) for url, bitrate in playlist_content]

        # Order by highest bitrate
        playlist_content.sort(key=lambda x: x[1], reverse=True)

        # Choose best video
        best_res = playlist_content[0][0]

        # return the best res video relative to the playlist
        return urljoin(playlist_url, best_res)

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

    def classes_to_media(self, classes):
        """
            retrive a filtered videos dict (see get_videos)
            and convert all player_urls to video_urls

            The function will return a sorted list of (fname, url)
        """

        videos = []
        for fname, player_url in classes.iteritems():
            videos.append((fname, self.player_url_to_media(player_url)))
        videos.sort(key=lambda x: x[0])
        return videos
