#!/usr/bin/env python
# -*- coding: utf-8 -*-
from contextlib import contextmanager
from werkzeug.local import Local, LocalManager
from importlib import import_module

from djangohotsauce.controllers.base import BaseController
from djangohotsauce.utils.django_settings import LazySettings
from djangohotsauce.utils.django_compat import get_resolver
from djangohotsauce.utils.django_compat import NoReverseMatch
from djangohotsauce.utils.log import configure_logging
log = configure_logging(__name__)
from djangohotsauce.utils.wsgilib import (
    HTTPRequest, 
    HTTPResponse,
    HTTPNotFound,
    HTTPUnauthorized,
    HTTPAuthenticationError,
    HTTPException
    )
from .utils import get_django_callable
from djangohotsauce.utils.template import direct_to_template

from authkit.authorize.exc import NotAuthenticatedError, NotAuthorizedError

RequestClass = HTTPRequest
_local = Local()

#_request = LocalProxy(lambda: get_current_request())

@contextmanager
def sessionmanager(request):
    _local.request = request
    yield
    _local.request = None

def get_current_request():
    try:
        return _local.request
    except AttributeError:
        raise TypeError("No request object for this thread")

__all__ = ('get_current_request', 'sessionmanager', 'WSGIController',)

class WSGIController(BaseController):

    _request_class = HTTPRequest
    _response_class = HTTPResponse

    def __init__(self, settings=None, enable_logging=True, 
        autoload=True, debug=False, environ=None):
        """
        Initializes a ``BaseController`` instance for processing
        standard Django view functions and handling basic error conditions.

        Available keyword arguments:

        - ``settings``: Django settings module (required)
        """
        self.logger = log
        if settings is not None:
            self.settings = settings
        else:
            self.settings = LazySettings()

        setattr(self, '_urlconf', self.settings.ROOT_URLCONF)
        setattr(self, '_resolver', get_resolver(self._urlconf, self.settings))
        self._resolver._urlconf_module = import_module(self._urlconf)
        
        # If using legacy autoload mecanism, attempt to register user-specified
        # wsgi callbacks. (DEPRECATED)
        #if (autoload and hasattr(self.settings, 'CUSTOM_ERROR_HANDLERS')):
        #    self.registerWSGIHandlers(self.settings.CUSTOM_ERROR_HANDLERS)


    def __call__(self, environ, start_response):
        """
        Override this to change the default request/response
        handling.

        This method is used for properly returning a WSGI response instance
        by calling ``get_response``.

        The latter does the grunt work of routing the request to the
        proper callable function or class.

        """
        req = self.init_request(self._request_class(environ=environ))
        with sessionmanager(req):
            _local.request = req
            self._request = req
            return self.get_response(req, start_response)

    def get_response(self, request, start_response):
        """Process ``path_url`` and return a callable function as
        the WSGI ``response`` callback.

        The callback view function is resolved using the built-in
        Django ``RegexURLResolver`` class.

        Returns a callable function (Response) or None if no
        view functions matched.

        See the docs in :djangohotsauce.utils.django_compat.RegexURLResolver:
        for details.

        This function may be overrided in custom subclasses to modify
        the response type.
        """
        #assert request == get_current_request()
        #assert isinstance(request, self._request_class), 'invalid request'
        try:
            try:
                response = get_django_callable(request, self._urlconf)
            except (NoReverseMatch, NotAuthorizedError):
                response = self.error(request, 404)
                request.environ['wsgi.error'] = 'User is not authenticated.'
                #response = self.error(request, 403)
        except (HTTPException, Exception):
            import traceback
            request.environ['wsgi.error'] = traceback.format_exc()
            response = self.error(request, 500)
        return response(request.environ, start_response)
    
    def error(self, request, code=None):
        if code is not None:
            name = 'error%s.mako' % code
        else:
            name = 'error500.mako'
        if 'wsgi.error' in request.environ.keys():
            error = request.environ['wsgi.error']
        else:
            error = "Server error (500)"
        return direct_to_template(request, name, extra_context={
            'error' : error}, status=code)

    def init_request(self, request):
        """A method to execute before ``process_request``"""
        # put handle404 and handle500 in request.environ
        #if hasattr(self, 'handle404'):
        #    self._environ['django.request.handle404'] = self.handle404
        #if hasattr(self, 'handle500'):
        #    self._environ['django.request.handle500'] = self.handle500
        request.environ['django.settings'] = self.settings
        #self._request = request
        return request
    
    @property
    def request(self):
        return self._request

    @property
    def response(self):
        return self._response

    @property
    def user(self):
        return self.request.get_user()

    def _environ_getter(self):
        """ Returns the current WSGI environment instance."""
        return getattr(self, '_environ', {})

    environ = property(_environ_getter)

    def _method_getter(self):
        return self.environ['REQUEST_METHOD']
    method = property(_method_getter)

    def _debug_getter(self):
        """Global debug flag. 
        Set settings.DEBUG to False to disable debugging"""
        return bool(self.settings.DEBUG == True)
    debug = property(_debug_getter)

    def _get_path_info(self, env):
        return str(env.get('PATH_INFO', ''))

