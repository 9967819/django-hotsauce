# This is the core test suite to port Django urls.py to Routes. YMMV
from test_support import unittest
from notmm.utils.urlmap import *

class RegexURLMapTestCase(unittest.TestCase):
    
    def setUp(self):
        # default behavior 
        self.urlmap = RegexURLMap()
    
    def tearDown(self):
        #self.urlmap.__del__()
        del self.urlmap

    #def test_label(self):
    #    # verifies the default label
    #    self.failUnlessEqual(repr(self.urlmap) == "<RegexURLMap: 'yadayada'>", repr(self.urlmap))

    def test_add_routes(self):
        urlmap = self.urlmap
        
        # XXX: Should we raise an RegexURLMapException here, as 'foobar' matches
        # nothing known ?
        urlmap.add_routes('sandbox.views', 
            url(r'^$', 'foobar', name="foobar"),
            url(r'^index.php$', 'index', name="index_php"),
            url(r'^test_db_session', 'test_session', name="test_session")
            )
        # Test adding another set of routes
        urlmap.add_routes('sandbox.handlers',
            url(r'^$', 'handle500', name="index2") # XXX: Should we raise
                                                   # RegexURLException here
                                                   # too, since we're creating
                                                   # a conflict. urlmap.routes
                                                   # must be a sequence of
                                                   # unique routes.
            )
        self.assertEqual(len(urlmap)==urlmap.__len__(), True)
    
    def test_include(self):
        # default string based include
        urlmap = RegexURLMap()
        urlmap.include('sandbox.config.urls')
        self.assertEqual(len(urlmap)==len(urlmap.routes), True, len(urlmap))
    
    #def test_autodiscover(self):
    #    # test the django admin configuration (autodiscovery of admin views)
    #    from django.contrib import admin
    #    admin.autodiscover()
    #    urlmap = RegexURLMap()
    #    urlmap.include(admin.site.urls, prefix='^admin/')
    #    self.assertEqual(len(urlmap.routes)>= 11, True)
        
    def test_commit(self):
        # raise an exception
        self.urlmap.include('sandbox.config.extras')
        self.urlmap.commit()
        self.failUnlessRaises(RegexURLMapException, self.urlmap.include, ('sandbox.config.urls'))

