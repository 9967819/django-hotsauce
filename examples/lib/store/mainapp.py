#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2008 Jack Bortone  <robillard.etienne@gmail.com>
# mainapp.py

#try:
#    import psyco
#    psyco.full()
#except ImportError:
#    pass

import os
import sys
#import webob
#from authkit.authenticate import middleware as authentication_middleware

#from tm.configuration import settings

from notmm.utils.wsgi           import IterableWSGIResponse
from notmm.utils.cutandpaste    import make_server, get_bind_addr
from notmm.utils.cutandpaste    import Banner
from notmm.utils.configparse    import loadconf
from notmm.controllers import *
#from wsgiref.validator import validate

from django.http import HttpRequest, HttpResponse, CompatCookie
from django.core.handlers.wsgi import WSGIRequest, WSGIHandler
from django.contrib.auth.models import AnonymousUser
from django.template import TemplateDoesNotExist, TemplateSyntaxError


class SatchmoController(WSGIController):

    def process_request(self, env):
        self._environ.update(env)
        self._request = self.request_class(env)
        self._request.environ = env.copy()
        #self._request.session = self.session

        self._request.path = env['PATH_INFO']
 
        from django.utils.importlib import import_module
        engine = import_module(self.settings.SESSION_ENGINE)
        session_key = self._request.COOKIES.get(self.settings.SESSION_COOKIE_NAME, None)
        self._request.session = engine.SessionStore(session_key)
        self._request.user = AnonymousUser()
        self._request.cookies = CompatCookie()
        
    def environ_getter(self):
        
        return self._environ

    environ = property(environ_getter)
    
    def __call__(self, env, start_response):

        try:
            self.process_request(env)
            response = super(SatchmoController, self).get_response(env, start_response)
        except (TemplateDoesNotExist, TemplateSyntaxError):
            #response = self.handle500(self.request)        
            #return response
            return process_exception(self.request, self.response_class)(env, start_response)
        start_response('200 OK', [('Content-Type', 'text/html')])
        return response



def exit(c):
    return os._exit(c)

def main(argv):
    """ a wrapper for running runserver """
    
    app_conf = loadconf('development.ini')
    
    # authkit user configuration variables are stored here
    auth_conf = app_conf['auth'] 

    wsgi_app = SatchmoController(
        global_conf='local_settings',
        request_class=WSGIRequest,
        response_class=HttpResponse,
        environ=app_conf, 
        #maintainer_mode=True
        )
    
    # Setup default callback functions to invoke for trapping
    # common exceptions
    #wsgi_app.sethandle('handle400', 'tm.handlers.handle400')
    #wsgi_app.sethandle('handle401', 'tm.handlers.handle401') # authkit needs this
    wsgi_app.sethandle('handle404', 'django.views.defaults.page_not_found')
    wsgi_app.sethandle('handle500', 'django.views.defaults.server_error')
    
    # Install the authentication middleware (LoginController)
    # wsgi_app = LoginController(wsgi_app, auth_conf)
    wsgi_app = SessionController(wsgi_app)

    bind_addr = get_bind_addr(app_conf)
    
    # Startup banner
    banner = Banner(sys.stderr, bind_addr=bind_addr)
    banner.show()
    
    conn = make_server(wsgi_app, bind_addr)
    try:
        conn.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        if 'close' in conn.__dict__:
            conn.close()
        print
        print 'bye.'
        exit(2)
    except IOError:
        raise

    exit(0)
        

if __name__ == "__main__":
   #assert len(sys.argv) >= 2, 'usage: runserver.py host:port' 
   main(argv=sys.argv)

