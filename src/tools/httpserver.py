#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Another stand-alone HTTP server for serving Django apps in pure
WSGI context with the ``wsgiref`` module. 
"""

import os
import sys
import importlib
import argparse

    
from djangohotsauce.utils.django_settings import LazySettings
#from djangohotsauce.utils.django_compat import get_callable
from djangohotsauce.utils.log import configure_logging
from djangohotsauce.utils.pastelib import eval_import
from djangohotsauce.http import get_bind_addr, daemonize
from djangohotsauce.controllers.wsgi import WSGIController
from djangohotsauce.release import BASE_REVISION, VERSION
#from djangohotsauce.adapters.utils import make_app

log = configure_logging('httpserver')

# quick and dirty logging dispatcher
_ = lambda x: log.debug(x)

def parse_cmdline(argv):
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('--debug', action="store_true", \
        help="Enable debugging mode", default=False)
    parser.add_argument('--port', action="store", \
        dest="port",
        nargs=1,
        help="HTTP port to accept connections. default: 8133",
        default=8133,
        )
    parser.add_argument('--host', action="store", \
        dest="host",
        nargs=1,
        help="Listening address. default: localhost",
        default="localhost",
        )
    parser.add_argument('-c', '--config', dest="filename",
        default="development.ini", nargs=1, \
        help="Path to a development.ini-like file")
    parser.add_argument('-s', '--ssl', action="store_true", \
        dest="enable_ssl", \
        help="Enable SSL transport mode (not implemented!)")
    parser.add_argument('--disable-auth', action="store_true", \
        dest="disable_auth", \
        help="Disable oauth2 middleware backend", default=True)
    parser.add_argument('--disable-xdserver', action="store_true", \
        dest="disable_xdserver", \
        help="Disable xdserver network database backend", default=False)
    parser.add_argument('--settings', dest="disable_settings", nargs=1, \
        required=False, help="TARGET settings module", default=False)
    # add support for custom PYTHONPATH 
    parser.add_argument('--pythonpath', dest="pythonpath", default=None, \
        required=False)
    
    # show version with --version
    parser.add_argument('--version', dest="version", action="store_true",
            help="Show the current version")

    # app_label hint:
    # ie: satchmo_store.wsgi.application
    parser.add_argument('--wsgi-app', dest="app_label",  
        required=True, help="WSGI callable to launch.")
    
    options = parser.parse_args(args=argv[1:])
    return options

def main(argv):
    options = parse_cmdline(sys.argv)

    if options.version:
        # print the current release and exit
        _("Django-hotsauce %s" % VERSION)
        sys.exit(0)

    if options.pythonpath is not None:
        for path in options.pythonpath.split(':'):
            sys.path.insert(0, path)

    # A INET4 address to bind to for listening for HTTP connections 
    bind_addr = (options.host[0], options.port[0])

    #if _settings.DEBUG: 
    #    #_('WSGIController class=%s' % repr(WSGIHandlerClass))
    #    _("%d settings found in module=%s" % (_settings.count(), repr(_settings)))
    #    _("Server address: %r" % repr(bind_addr))

    #wsgi_app = make_app(options.app_label, _settings)
    #if have_oauthclient == True:
    #   from djangohotsauce.controllers.oauth import OAuthController
    #    client = GoogleClient(
    #        google,
    #        _settings.OAUTH2_CLIENT_ID,
    ##        _settings.OAUTH2_ACCESS_TOKEN,
    #        _settings.OAUTH2_SCOPE, 
    #        _settings.OAUTH2_REDIRECT_URL,
    #        )
    #    wsgi_app = OAuthController(wsgi_app, client)
    modname, modfunc = options.app_label.rsplit('.',1)
    wsgi_app = getattr(
        importlib.import_module(modname),
        modfunc
        )
    daemonize(wsgi_app, bind_addr)

if __name__ == "__main__":
    #assert len(sys.argv) >= 2, 'usage: runserver.py host:port' 
    main(argv=sys.argv)

