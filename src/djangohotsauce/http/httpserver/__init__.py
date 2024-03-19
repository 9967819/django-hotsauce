#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""WSGI helper functions and classes for development purposes.

"""
import sys
import importlib
import urllib
import logging
import time
import platform
import werkzeug
python_impl = platform.python_implementation()

#from wsgiref import simple_server, validate

from djangohotsauce.utils.log import configure_logging
from djangohotsauce.utils.configparse import string_getter, int_getter
from djangohotsauce.utils.wsgilib import translogger 
from djangohotsauce.release import BASE_REVISION, RELEASE_NAME
from django.utils.termcolors import colorize as _colored
    
from .reloader import install

log = configure_logging('httpserver')

__all__ = ('WSGIServerBase', 'BannerBase', 'get_bind_addr', 'daemonize')

class BannerBase(object):
    """This is a simple startup banner.

    Usage:
        >>> banner = BannerBase(fp=sys.stderr, ('127.0.0.1', '8000'))
        >>> banner.show()
    """

    default_format = "%Y-%m-%d %H:%M:%S %Z %z"
    debug_msg_handler = log.debug

    def __init__(self, fp=debug_msg_handler, bind_addr=('127.0.0.1', '8000'),
                 settings=None):
        self.bind_addr = bind_addr #TODO: use default_bind_addr
        print(bind_addr)
        fmt = self.get_default_format(settings)
        self.start_time = time.strftime(fmt)
        self.server_uri = 'http://%s:%i/' % (bind_addr[0], int(bind_addr[1]))
        #if not isinstance(self.bind_addr, tuple):
        #    raise ValueError("Error: invalid bind_addr type: %r" \
        #        % type(self.bind_addr))

        #assert len(self.bind_addr) == 2, \
        #    'bind_addr must contains exactly two elements'

    def get_default_format(self, settings):
        try:
            fmt = settings.DATETIME_INPUT_FORMATS[0]
        except (AttributeError, IndexError):
            return self.default_format
        else:
            return fmt
    
    def debug(self, message, color='cyan', **kwargs):
        """Write a string to the terminal with colored output"""
        self.debug_msg_handler(message)

    def show(self):
        """Override this method to handle the formatting of the banner"""

        print("Initializing on %s" % self.start_time)
        print("Starting HTTP server on %s" % self.server_uri)
        #colored("djangohotsauce %s "%(notmm.__version__)) 
        #colored("%s"%djangohotsauce.__copyright__)
        # XXX this part need more work ! :)
        print("Django-hotsauce release %s (%s)" % (
            BASE_REVISION, RELEASE_NAME
            ))
        return self

class WSGIServerBase(object):
    """Wrapper class to configure a simple HTTP server instance"""
    
    # Uncomment this to enable cherrypy based http daemon
    # serverClass = wsgiserver.CherryPyWSGIServer
    
    serverClass = werkzeug.run_simple # wsgiref
    
    def __init__(self, wsgi_app, bind_addr, debug=True):
        """HTTPServer.__init__"""
        self.host = bind_addr[0]
        self.port = int(bind_addr[1])
        self.wsgi_app = wsgi_app
        if debug:
            # run the wsgi app in using wsgiref validator
            # middleware
            self.request_handler = validate.validator(wsgi_app)
        else:
            self.request_handler = wsgi_app

        #
        b = BannerBase(bind_addr=bind_addr)
        b.show()
    
        self.server = self.serverClass.make_server(self.host, self.port, self.request_handler)

    def serve(self):
        while True:
            try:
                self.server.serve_forever()
            except SystemExit:
                self.server.close()
                sys.exit(0)

def get_bind_addr(app_conf, section='httpserver', listen_port=8000):
    """
    Return a 2-element tuple containing the hostname and port
    to listen for remote connections.
    """

    host = string_getter(app_conf, section, 'host') or urllib.localhost()
    port = int_getter(app_conf, section, 'port') or listen_port

    return (host, port)

def daemonize(wsgi_app, bind_addr, logging=True, autoreload=True, 
    debug=True):
    """
    Create an instance of a validating WSGI server for 
    development purposes.
    
    XXX: enabling WSGI validation (debug=True) may trigger
    a deadlock for POST input data processing.
    """
    
    # Install translogger middleware if logging is enabled
    if logging:
        request_handler = translogger.TransLogger(wsgi_app)
    else:
        request_handler = wsgi_app
    
    # Add optional autoreloading support (see the docstring for help
    # on installing this)
    if autoreload:
        try:
            install()
        except ImportError:
            pass

    # init the wsgi server 
    server = WSGIServerBase(request_handler, bind_addr, debug=debug)

    try:
        while True:
            server.serve()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except:
        raise

main = daemonize

