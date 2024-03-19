#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Require MoinMoin 1.8.9
from MoinMoin.server.server_wsgi import moinmoinApp
from notmm.controllers.base import BaseController
import logging
log = logging.getLogger(__name__)

__all__ = ['MoinMoinController']


class MoinMoinController(BaseController):
    """
    A BaseController extension serving a MoinMoin wiki app.
    """
    #debug = False
    #logger = log

    def application(self, environ, start_response):
        """Creates a mini MoinMoin wiki handler with generic file 
        upload support.

        """
        return moinmoinApp(environ, start_response)
