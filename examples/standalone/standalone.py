#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Self-contained demo script that bootstraps the helloworld
app and launch a WSGI server on localhost:8000. 

"""

import sys, os, logging
#Setup logging
log = logging.getLogger('notmm.controllers.wsgi')

from notmm.utils.django_settings import LazySettings
from notmm.utils.configparse import has_conf, loadconf
from notmm.http import get_bind_addr, HTTPServer

settings = LazySettings()

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

    if settings.DEBUG:
        log.debug("Found %d settings!"%settings.count())

    # setup default controller options
    from demo_app import WSGIApplication as WSGIApp
    wsgi_app = WSGIApp(settings=settings, app_conf=app_conf)
 
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
