#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo wiki using MoinMoinController request handler.

Copyright (C) 2010-2011 Jack Bortone <jack@isotopesoftware.ca>
All rights reserved.
"""

import sys, os
import logging

#from MoinMoin.server.server_wsgi import WsgiConfig
#XXX this require MoinMoin-1.8.9. The request package has been
#deprecated in MoinMoin-1.9.x.
from MoinMoin.request import request_wsgi

examples_dir = os.getcwd()
sys.path.extend([
    os.path.join(examples_dir, 'lib'),
    os.path.join(examples_dir, 'lib/site-packages')
    ])

import wikiapp
from notmm.http.httpserver import daemonize, get_bind_addr

# Add the wikiconfig module in sys.path if not present
if not 'wikiconfig' in sys.modules:
    sys.path.insert(-1, wikiapp.default_instance)
    import wikiconfig
    print "found correct wikiconfig!"

app_conf = wikiapp.global_conf['wikiapp']
#print app_conf

# Check if moin.url_prefix_static has been defined
# in development.ini, otherwise use the default (/moin_static184).
url_prefix_static = app_conf.get('moin.url_prefix_static', '/moin_static184')
wsgi_request_class = getattr(request_wsgi, 'Request')  
#response_class = HTTPResponse

from MoinMoin.server import Config as WsgiConfig

class WikiConfig(WsgiConfig):
    url_prefix_static = url_prefix_static

def main():
    #init the config instance
    config = WikiConfig()
    #init the main response handler
    wsgi_app = wikiapp.MoinMoinController(settings=config, app_conf={
        'django.settings_autoload' : False,
        'wsgi.request_class' : wsgi_request_class,
        'logging.disabled'   : True})
    
    # get the default inet address to bind the wsgi server to
    bind_addr = get_bind_addr(wikiapp.global_conf)
    
    # start the wsgi server
    s = daemonize(wsgi_app, bind_addr)
    s.serve_forever()

if __name__ == '__main__':
    main()
