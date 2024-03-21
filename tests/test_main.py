#!/usr/bin/env python
import os
import sys
import unittest
from djangohotsauce.controllers.wsgi import WSGIController
from djangohotsauce.test import ControllerTestCase

import local_settings

class SimpleController(WSGIController):
    minversion = "5.0.3"

class SimpleControllerTestCase(ControllerTestCase):

    def setUp(self):

        os.environ['DJANGO_SETTINGS_MODULE'] = 'local_settings'
    
    def test_init_main(self):
        
        wsgi_app = WSGIController(settings=local_settings)
        from django import VERSION
        from djangohotsauce.release import version
        print("Django version: %d.%d.%d" % (VERSION[0], VERSION[1], VERSION[2]))
        print("Django-hotsauce version: %d.%d.%d" % (version[0], version[1], version[2]))
        print("Python version: %s" % sys.version)

if __name__ == '__main__':
    unittest.main()

