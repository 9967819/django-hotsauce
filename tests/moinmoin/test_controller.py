#!/usr/bin/env python
# Copyright (C) 2007-2009 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.

import sys
import wikiapp

from MoinMoin import log
from MoinMoin.request import request_wsgi
from MoinMoin.server import Config

from test_support import (
    BaseControllerTestCase, 
    TestClient, 
    unittest,
    make_app,
    settings
    )

if not 'wikiconfig' in sys.modules:
    default_instance = wikiapp.default_instance
    sys.path.insert(-1, default_instance)

import wikiconfig

# Disables spurious log messages while running the testsuite
# logger = log.getLogger(__name__)
# logger.root.setLevel('INFO')
class WikiConfig(Config):
    pass

class MoinMoinControllerTestCase(BaseControllerTestCase):

    wsgi_app = wikiapp.MoinMoinController
    #settingsClass = LazySettings
    
    def setUp(self):    
        #debug_level=2 enables interactive pdb hook
        self.wikiconfig = WikiConfig()
        self.callback = self.wsgi_app(settings=settings)
        self.client = TestClient(self.callback)
        
    def test_application(self):
        req = self.client.request
        response = self.client.get('/')
        self.assertEqual(response.status_code, '200 OK')
        
#def main():
#    c = WikiConfig()
#    application = WikiController(c)
#    # fastcgi here
#    server = fastcgi.ForkingWSGIServer(wsgi_app, workers=2)
#    server.serve_forever()


