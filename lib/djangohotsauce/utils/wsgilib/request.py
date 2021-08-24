#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import copy
#from werkzeug.local import Local
try:
    #Py3
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus

from werkzeug.wrappers import BaseRequest
from werkzeug.formparser import parse_form_data
from werkzeug.datastructures import ImmutableMultiDict

__all__ = ['HTTPRequest']

class HTTPRequest(BaseRequest):

    def __init__(self, environ={}, populate_request=True, shallow=True, **kwargs):
        """provide a generic environment for HTTP requests"""
        super(HTTPRequest, self).__init__(environ, populate_request=populate_request, shallow=shallow, **kwargs)
        self._environ = environ.copy()
        
    def get_user(self):
        """Returns the current user as defined in environ['REMOTE_USER'] or
        None if not set"""
        if 'REMOTE_USER' in self._environ:
            return self.environ['REMOTE_USER']
        else:
            return 'Guest'
    @property
    def user(self):
        return self.get_user()

    def get_full_path(self):
        """Return the value of PATH_INFO, a web browser dependent
        HTTP header, or None if the value is not set"""

        try:
            p = unquote_plus(self.environ['PATH_INFO'])
        except KeyError:
            # invalid CGI environment
            return None
        return p    
            
    def get_POST(self):
        """Extracts data from a POST request
        Returns a dict instance with extracted keys/values pairs."""
        if not (self.method == 'POST' or 'wsgi.input' in self.environ):
            return ImmutableMultiDict({})
        fs_environ = self.environ.copy()
        stream, form, files = parse_form_data(fs_environ)
        return ImmutableMultiDict(form)

    # extra public methods borrowed from Django
    def is_ajax(self):
        """check if the http request was transmitted with asyncronous (AJAX) transport"""
        if 'HTTP_X_REQUESTED_WITH' in self.environ:
            if self.environ['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest':
                return True
        #print 'not ajax'        
        return False        

    
    def is_secure(self):
        return bool(self.environ.get("HTTPS") == "on")
    
    @property
    def method(self):
        return str(self.environ.get('HTTP_METHOD', None))
    
    @property
    def POST(self):
        return self.get_POST()
    
    @property
    def GET(self):
        return self.args

    path_url = property(get_full_path)
