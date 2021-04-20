#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from notmm.controllers.schevo  import SchevoController
from notmm.utils.configparse   import loadconf
from notmm.utils.wsgilib       import HTTPRequest, HTTPResponse
from werkzeug.test import create_environ
from test_support import (
    BaseControllerTestCase, TestClient,
    settings,
    setup_test_handlers
    )

def get_app_conf(section):
    return loadconf('development.ini', section=section)

class SchevoControllerTestCase(BaseControllerTestCase):

    wsgi_app = SchevoController
    response_class = HTTPResponse

    def __init__(self, methodName='runTest'):

        super(BaseControllerTestCase, self).__init__(methodName)

        self.request = HTTPRequest(create_environ())

    def setUp(self):
        self.callback = self.wsgi_app(
            #the HTTP request obj for testing
            self.request,
            settings.SCHEVO['DATABASE_NAME']
            )
        setup_test_handlers(self.callback, settings)
        self.client = TestClient(self.callback)

    def tearDown(self):
        self.callback = None

    def test_with_schevo_database(self):
        response = self.client.post('/test_post')
        self.assertEqual(response[1] == '200 OK', True)


