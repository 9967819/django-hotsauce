#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2007-2013 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.
# Please see the files "LICENSE" and "NOTICE" for details.
###
"""
Self-contained demo script that bootstraps the helloworld
app and launch a WSGI server on localhost:8000. 

"""

import sys, os, logging
log = logging.getLogger('notmm')

from notmm.utils.django_settings import SettingsProxy
from notmm.utils.configparse import has_conf, loadconf
from notmm.http import get_bind_addr, HTTPServer

from wsgi_oauth2 import client

class ConfigurationError(Exception):
    pass

if has_conf(os.getcwd(), 'development.ini'):
    app_conf = loadconf('development.ini')
    # Get the host/port using get_bind_addr.
    bind_addr = get_bind_addr(app_conf, 'httpserver')
else:
    raise ConfigurationError('development.ini not found!')

def main(app_label):
    """Launch a simple WSGI app in stand-alone mode. 
    
    """
    # Setup basic site environment
    #configure_minimal_env()
    sys.path.extend(['lib', 'lib/site-packages'])

    settings = SettingsProxy(os.environ['DJANGO_SETTINGS_MODULE'], \
        autoload=True).get_settings()
    if settings.DEBUG:
        log.debug("Found %d settings!"%settings.count())

    # setup default controller options
    from demo_app import WSGIApplication as WSGIApp
    wsgi_app = WSGIApp(settings)
    google_client = client.GoogleClient(
        settings.OAUTH2_CLIENT_ID,
        access_token=settings.OAUTH2_ACCESS_TOKEN, 
        scope='email', 
        redirect_url=settings.OAUTH2_REDIRECT_URL,
        login_path="/session_login/")

    wsgi_app = google_client.wsgi_middleware(wsgi_app, secret=settings.SECRET_KEY)

    # Install some handlers; We can skip this part if the
    # controller instance has them configured already.
    #wsgi_app.sethandle('handle404', app_label + '.handlers.handle404')
    #wsgi_app.sethandle('handle500', app_label + '.handlers.handle500')
    #import pdb; pdb.set_trace()
    WSGIServer = HTTPServer(wsgi_app, bind_addr)

    try:
        log.info("Starting HTTP server on %s:%d" % bind_addr)
        WSGIServer.serve()
    except (SystemExit, KeyboardInterrupt):
        log.info('Shutting down HTTP server...')
        sys.exit(2)

if __name__ == '__main__':
    main(app_label='helloworld')
