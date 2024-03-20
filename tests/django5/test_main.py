#!/usr/bin/env python
import os
import unittest
from djangohotsauce.controllers.wsgi import WSGIController


class SimpleController(WSGIController):
    minversion = "5.0.3"

class ControllerTestCase(unittest.TestCase):

    def setUp(self):

        os.environ['DJANGO_SETTINGS_MODULE'] = 'local_settings'
    
    def test_init_main(self):
        
        wsgi_app = WSGIController()





