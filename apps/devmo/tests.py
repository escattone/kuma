import csv
import shlex
import urllib2
from os.path import basename, dirname, isfile, isdir

from mock import patch
from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from pyquery import PyQuery as pq
import test_utils

from devmo.helpers import devmo_url
from devmo import urlresolvers
from devmo.models import Calendar, Event

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse

from nose.plugins.skip import SkipTest

class SkippedTestCase(test_utils.TestCase):
    def setUp(self):
        raise SkipTest()

def parse_robots(base_url):
    """ Given a base url, retrieves the robot.txt file and
        returns a list of rules. A rule is a tuple.
        Example:
        [("User-Agent", "*"), ("Crawl-delay", "5"),
         ...
         ("Disallow", "/template")]

        Tokenizes input to whitespace won't break
        these acceptance tests.
    """
    rules = []
    robots = shlex.shlex(urllib2.urlopen("%s/robots.txt" % base_url))
    robots.whitespace_split = True
    token = robots.get_token()
    while token:
        rule = None
        if token[-1] == ':':
            rule = (token[0:-1], robots.get_token())
        if rule:
            rules.append(rule)
        token = robots.get_token()
    return rules


class TestDevMoRobots(test_utils.TestCase):
    """ These are really acceptance tests, but we seem to lump
        together unit, integration, regression, and
        acceptance tests """
    def test_production(self):
        rules = [
            ("User-Agent", "*"),
            ("Crawl-delay", "5"),
            ("Sitemap", "sitemap.xml"),
            ("Request-rate", "1/5"),
            ("Disallow", "/@api/deki/*"),
            ("Disallow", "/*feed=rss"),
            ("Disallow", "/*type=feed"),
            ("Disallow", "/skins"),
            ("Disallow", "/template:"),
        ]
        eq_(parse_robots('http://developer.mozilla.org'),  rules)
        eq_(parse_robots('https://developer.mozilla.org'), rules)

    def test_stage_bug607996(self):
        rules = [
            ("User-agent", "*"),
            ("Disallow", "/"),
        ]

        # TODO: update to kuma when kuma staging server is up
        #No https://mdn.staging.mozilla.com, this serves up Sumo
        eq_(parse_robots('http://mdn.staging.mozilla.com'), rules)

        eq_(parse_robots('https://developer-stage.mozilla.org'), rules)
        eq_(parse_robots('http://developer-stage.mozilla.org'),  rules)

        eq_(parse_robots('https://developer-stage9.mozilla.org'), rules)
        eq_(parse_robots('http://developer-stage9.mozilla.org'),  rules)


class TestDevMoHelpers(test_utils.TestCase):
    def test_devmo_url(self):
        en_only_page = '/en/HTML/HTML5'
        localized_page = '/en/HTML'
        req = test_utils.RequestFactory().get('/')
        context = {'request': req}

        req.locale = 'en-US'
        eq_(devmo_url(context, en_only_page), en_only_page)
        req.locale = 'de'
        eq_(devmo_url(context, localized_page), '/de/HTML')
        req.locale = 'zh-TW'
        eq_(devmo_url(context, localized_page), '/zh_tw/HTML')


class TestDevMoUrlResolvers(test_utils.TestCase):
    def test_prefixer_get_language(self):
        # language precedence is GET param > cookie > Accept-Language
        req = test_utils.RequestFactory().get('/', {'lang': 'es'})
        prefixer = urlresolvers.Prefixer(req)
        eq_(prefixer.get_language(), 'es')

        req = test_utils.RequestFactory().get('/')
        req.COOKIES['lang'] = 'de'
        prefixer = urlresolvers.Prefixer(req)
        eq_(prefixer.get_language(), 'de')

        req = test_utils.RequestFactory().get('/')
        req.META['HTTP_ACCEPT_LANGUAGE'] = 'fr'
        prefixer = urlresolvers.Prefixer(req)
        eq_(prefixer.get_language(), 'fr')

APP_DIR = dirname(__file__)
MOZILLA_PEOPLE_EVENTS_CSV = '%s/fixtures/Mozillapeopleevents.csv' % APP_DIR
XSS_CSV = '%s/fixtures/xss.csv' % APP_DIR
BAD_DATE_CSV = '%s/fixtures/bad_date.csv' % APP_DIR

class TestCalendar(test_utils.TestCase):

    def setUp(self):
        self.cal = Calendar.objects.get(shortname='devengage_events')
        self.event = Event(date="2011-06-17", conference="Web2Day",
                           location="Nantes, France",
                           people="Christian Heilmann",
                           description="TBD", done="no", calendar=self.cal)
        self.event.save()

    def test_reload_bad_url_does_not_delete_data(self):
        self.cal.url = 'bad'
        success = self.cal.reload()
        ok_(success == False)
        ok_(Event.objects.all()[0].conference == 'Web2Day')
        self.cal.url = 'http://test.com/testcalspreadsheet'
        success = self.cal.reload()
        ok_(success == False)
        ok_(Event.objects.all()[0].conference == 'Web2Day')

    def test_reload_from_csv_data(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # check total
        assert_equal(33, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_reload_from_csv_data_blank_end_date(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # check total
        assert_equal(33, len(Event.objects.all()))
        # spot-check
        event = Event.objects.get(conference='Monash University')
        ok_(event)
        eq_(None, event.end_date)

    def test_bad_date_column_skips_row(self):
        self.cal.reload(data=csv.reader(open(BAD_DATE_CSV, 'rb')))
        # check total - should still have the good row
        assert_equal(1, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_html_santiziation(self):
        self.cal.reload(data=csv.reader(open(XSS_CSV, 'rb')))
        # spot-check
        eq_('&lt;script&gt;alert("ruh-roh");&lt;/script&gt;Brendan Eich',
            Event.objects.get(conference="Texas JavaScript").people)

class CalendarViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    def test_events(self):
        url = reverse('events')
        r = self.client.get(url)
        d = pq(r.content)
        eq_(200, r.status_code)
        eq_("Where is Mozilla?", d('h1.page-title').text())
