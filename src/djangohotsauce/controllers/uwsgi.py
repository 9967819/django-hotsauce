#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007-2017 Jack Bortone <tkadm30@yandex.ru>
# All rights reserved.
"""uWSGIController API Version 0.9.1

Middleware for storing uWSGI statistics into the environ object.
"""

import sys
import logging
import demjson
import urllib

logger = logging.getLogger(__name__)

from djangohotsauce.controllers.wsgi import WSGIController

__all__ = ('uWSGIController',)


class uWSGIController(WSGIController):

    def __init__(self, wsgi_app=None, settings=None, app_conf=None, stats_url='http://localhost:9001'):
    
        self.wsgi_app = wsgi_app
        self.stats_url = stats_url
        super(uWSGIController, self).__init__(settings=settings, app_conf=app_conf) # hack

    def init_request(self, request):
        #logger.debug('In uWSGIController.init_request...')
        request.environ['uwsgi.requests'] = self.connections(self.stats_url)
        self._request = request
        self._environ = request.environ
        return self._request
    
    def connections(self, url):
        """Return the amount of live connections (requests) for all workers"""
        try:
            fp = urllib.urlopen(url)
        except IOError:
            return 0
        json = demjson.decode(fp.read())

        connections = 0

        for worker in json['workers']:
            connections += worker['requests']
        
        fp.close()

        return connections

