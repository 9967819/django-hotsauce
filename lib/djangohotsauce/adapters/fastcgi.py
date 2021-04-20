#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
#import fastcgi
import mainapp # global_conf setup
#import logging
from djangohotsauce.controllers.wsgi import WSGIController
from utils import make_app
from gevent_fastcgi.server import FastCGIServer
from gevent_fastcgi.wsgi import WSGIRequestHandler
#log = logging.getLogger('djangohotsauce.controllers.wsgi')

def initmain(WSGIHandlerClass=WSGIController):

    
    # check for i18n 
    #if bool(mainapp.global_conf['mainapp']['i18n.enable'] == 'true'):
    #    try:
    #        from djangohotsauce.controllers.i18n import I18NController as WSGIHandlerClass
    #    except ImportError:
    #        log.debug('generic i18n support is disabled')
    
    wsgi_app = make_app(handlerClass=WSGIHandlerClass)

    # fastcgi
    #import pdb; pdb.set_trace()
    #s = fastcgi.ForkingWSGIServer(wsgi_app, workers=1)
    #s.serve_forever()
    handler = WSGIRequestHandler(wsgi_app)
    s = FastCGIServer(('127.0.0.1', 8808), handler)
    s.serve_forever()
    #return wsgi_app

if __name__ ==  '__main__':
    initmain()
