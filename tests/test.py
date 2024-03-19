#!/usr/bin/env python3
"""Summer is beautiful..."""
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'local_settings'

from djangohotsauce.controllers.wsgi import WSGIController

if __name__ == '__main__':
    wsgi_app = WSGIController()
    print(wsgi_app)
