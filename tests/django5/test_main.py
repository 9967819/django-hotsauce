#!/usr/bin/env python
import os
from djangohotsauce.controllers.wsgi import WSGIController


class SimpleController(WSGIController):
    minversion = "5.0.3"

    def setUp():

        os.environ['DJANGO_SETTINGS_MODULE'] = 'local_settings'
    def test_init_main():
        
        pass




