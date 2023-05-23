#!/usr/bin/env python
# new code :)

import random
import logging
import hmac
import hashlib
import base64
import html

try:
    # python3   
    from urllib.parse import urlparse, urljoin, parse_qs
except ImportError:
    from urlparse import urlparse, urljoin, parse_qs

try:
    # python3
    from http.cookies import SimpleCookie
except ImportError:
    from Cookie import SimpleCookie

from djangohotsauce.controllers.wsgi import WSGIController
import pickle as pickle
            
log = logging.getLogger(__name__)

__all__ = ['OAuthResponseMiddleware']    

class OAuthResponseMiddleware(object):
    """WSGI middleware application.

    :param client: oauth2 client
    :type client: :class:`Client`
    :param application: wsgi application
    :type application: callable object
    :param secret: secret key for generating HMAC signature
    :type secret: :class:`bytes`
    :param path: path prefix used for callback. by default, a randomly
                 generated complex path is used
    :type path: :class:`basestring`
    :param cookie: cookie name to be used for maintaining the user session.
                   default is :const:`DEFAULT_COOKIE`
    :type cookie: :class:`basestring`
    :param set_remote_user: Set to True to set the REMOTE_USER environment
                            variable to the authenticated username (if supported
                            by the :class:`Service`)
    :type set_remote_user: :class:`bool`
    :param forbidden_path: What path should be used to display the 403 Forbidden
                           page.  Any forbidden user will be redirected to this
                           path and a default 403 Forbidden page will be shown.
                           To override the default Forbidden page see the
                           ``forbidden_passthrough`` option.
    :type forbidden_path: :class:`basestring`
    :param forbidden_passthrough: Should the forbidden page be passed-through to
                                  the protected application. By default, a
                                  generic Forbidden page will be generated. Set
                                  this to :const:`True` to pass the request
                                  through to the protected application.
    :type forbidden_passthrough: :class:`bool`
    :param login_path:  The base path under which login will be required. Any
                        URL starting with this path will trigger the OAuth2
                        process.  The default is '/', meaning that the entire
                        application is protected.  To override the default
                        path see the :attr:`login_path` option.
    :type login_path: :class:`basestring`

    .. versionadded:: 0.1.4
       The ``login_path`` option.

    .. versionadded:: 0.1.3
       The ``forbidden_path`` and ``forbidden_passthrough`` options.

    .. versionadded:: 0.1.2
       The ``set_remote_user`` option.

    """

    #: (:class:`basestring`) The default name for :attr:`cookie`.
    DEFAULT_COOKIE = 'wsgioauth2sess'


    #: (:class:`basestring`) The path that is used to display the 403 Forbidden
    #: page.  Any forbidden user will be redirected to this path and a default
    #: 403 Forbidden page will be shown.  To override the default Forbidden
    #: page see the :attr:`forbidden_passthrough` option.
    forbidden_path = "/forbidden"

    #: (:class:`bool`) Whether the forbidden page should be passed-through
    #: to the protected application.   By default, a generic Forbidden page
    #: will be generated.  Set this to :const:`True` to pass the request
    #: through to the protected application.
    forbidden_passthrough = False

    #: (:class:`basestring`) The base path under which login will be required.
    #: Any URL starting with this path will trigger the OAuth2 process.  The
    #: default is '/', meaning that the entire application is protected.  To
    #: override the default path see the :attr:`login_path` option.
    #:
    #: .. versionadded:: 0.1.4
    login_path = ['/blog/admin/create/']

    def __init__(self, 
        client=None, 
        secret=None,
        client_token=None,
        client_token_secret=None,
        path="/oauth2callback", 
        cookie=DEFAULT_COOKIE, 
        set_remote_user=True, 
        ):

        self.wsgi_app = WSGIController()
        self.client = client
        #assert getattr(self.client, 'token') != None, 'invalid access token!'
        self.secret = secret
        self.path = path
        
        self.set_remote_user = set_remote_user
        
        self.cookie = cookie
        self.cookie_dict = SimpleCookie()
        self._environ = {}
        self.request = None

    def sign(self, value):
        """Generate signature of the given ``value``.

        .. versionadded:: 0.2.0

        """
        #print(value)
        return hmac.new(value).hexdigest()

    def redirect(self, url, start_response, headers={}):
        h = {'Content-Type': 'text/html; charset=utf-8', 'Location': url}
        h.update(headers)
        start_response('307 Temporary Redirect', list(h.items()))
        e_url = html.escape(url).encode('iso-8859-1')
        yield b'<!DOCTYPE html>'
        yield b'<html><head><meta charset="utf-8">'
        yield b'<meta http-equiv="refresh" content="0; url='
        yield e_url
        yield b'"><title>Redirect to '
        yield e_url
        yield b'</title></head><body><p>Redirect to <a href="'
        yield e_url
        yield b'">'
        yield e_url
        yield b'</a>&hellip;</p></body></html>'

    def forbidden(self, start_response):
        """Respond with an HTTP 403 Forbidden status."""
        h = [('Content-Type', 'text/html; charset=utf-8')]
        start_response('403 Forbidden', h)
        yield b'<!DOCTYPE html>'
        yield b'<html><head><meta charset="utf-8">'
        yield b'<title>Forbidden</title></head>'
        yield b'<body><p>403 Forbidden - '
        yield b'Your account does not have access to the requested resource.'
        yield b'<pre>'
        yield b'</pre>'
        yield b'</p></body></html>'

    def __call__(self, environ, start_response):
        url = '{0}://{1}{2}'.format(environ.get('wsgi.url_scheme', 'http'),
                                    environ.get('HTTP_HOST', ''),
                                    environ.get('PATH_INFO', ''))
        

        path = environ['PATH_INFO']
        redirect_uri = urljoin(url, path)
        forbidden_uri = urljoin(url, self.forbidden_path)
        query_string = environ.get('QUERY_STRING', None)
        #session = None
        environ['wsgi.request'] = self.request
        
        if query_string is not None:
            url += '?' + query_string
            query_dict = parse_qs(query_string)
        else:
            query_dict = dict()
        
        if 'HTTP_COOKIE' in environ:
            self.cookie_dict.load(environ['HTTP_COOKIE'])

        
        if (self.forbidden_passthrough is True 
            and not path in self.login_path):
            # Pass the forbidden request through to the app
            return self.wsgi_app(environ, start_response)
        elif path.startswith(self.path):
            #/oauth2callback
            code = query_dict['code']
            try:
                code = code[0]
                access_token = self.client.request_access_token(
                        redirect_uri, client_token, client_token_secret, code)
            except TypeError as e:
                return self.forbidden(start_response)
                
            # Load the username now so it's in the session cookie
            #log.debug(access_token)
            if self.set_remote_user:
                log.debug("Setting remote user name now...")
                #log.debug("sending token: %s" %access_token)
                #log.debug(access_token)
                token = self.client.load_username(access_token)
            
            # Check if the authenticated user is allowed
            if not self.client.is_user_allowed(access_token):
                return self.redirect(forbidden_uri, start_response)

            session = pickle.dumps(access_token)
            sig = self.sign(session)
            signed_session = sig.encode('ascii') + b',' + session
            signed_session = base64.urlsafe_b64encode(signed_session)
            set_cookie = SimpleCookie()
            set_cookie[self.cookie] = signed_session.decode('ascii')
            set_cookie[self.cookie]['path'] = '/'
            if 'expires_in' in access_token:
                expires_in = int(access_token['expires_in'])
                set_cookie[self.cookie]['expires'] = expires_in
                set_cookie = set_cookie[self.cookie].OutputString()
            return self.redirect(query_dict.get('state', [''])[0],
                                 start_response,
                                 headers={'Set-Cookie': set_cookie})
        elif path in self.login_path:
            #XXX entry point - protected uri
            session = None
            if self.cookie in self.cookie_dict:
                session = self.cookie_dict[self.cookie].value
                try:
                    session = base64.urlsafe_b64decode(session)
                except binascii.Error:
                    session = b''
                if b',' in session:
                    sig, val = session.split(b',', 1)
                    if sig.decode('ascii') == self.sign(val):
                        try:
                            session = pickle.loads(val)
                        except (pickle.UnpicklingError, ValueError):
                            session = None
            if session is None:
                access_token = self.client.request_access_token(
                    redirect_uri, self.client.request_token, self.client.request_token_secret, code=url)
                session = self.client.load_username(access_token)
                print(session)
                print("hello")
                environ['wsgioauth2.session'] = session
                if self.set_remote_user and 'name' in session:
                    environ['REMOTE_USER'] = session['name']
                    self.session = session
        return self.wsgi_app(environ, start_response)

