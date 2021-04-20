#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import os
#import traceback
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest


from notmm.controllers.base import BaseController
from notmm.controllers.wsgi import WSGIController
from notmm.utils.django_settings import LazySettings
from notmm.utils.wsgilib         import HTTPRequest, HTTPResponse
from werkzeug.test import Client as TestClient

settings = LazySettings()

ResponseClass = HTTPResponse
RequestClass = HTTPRequest

#import logging_conf, logging
#logger = logging.getLogger(__name__)

def make_app(callback, *args, **kwargs):
    return callback(*args, **kwargs)

def setup_test_handlers(callback, settings):
    #if settings.DEBUG:
    #    print('function %s registered to %s' % (func_name, module))
    callback.registerWSGIHandlers(settings.CUSTOM_ERROR_HANDLERS)
    return None

def inittestpackage():
    if 'settings' in sys.modules:
        del sys.modules['settings']


class DjangoTestCase(unittest.TestCase):
    def setUp(self):
        import django
        django.setup()

# default test controller

class BaseControllerTestCase(unittest.TestCase):
    wsgi_app = BaseController

    def setUp(self):
        self.callback = self.wsgi_app() #self.wsgi_app()
        self.client = TestClient(self.callback)
        #setup_test_handlers(self.callback, settings)

    def tearDown(self):
        pass

class WSGIControllerTestCase(BaseControllerTestCase):
    # Core tests for the WSGIController extension
    wsgi_app = WSGIController
