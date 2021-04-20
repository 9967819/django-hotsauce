#!/usr/bin/env python
import sys
import json
import logging
import requests
from werkzeug.datastructures import ImmutableDict
from djangohotsauce.utils.wsgilib import HTTPException
log = logging.getLogger(__name__)

PY3K = sys.version_info[0] == 3

if PY3K:
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError
else:
    # python27
    from urllib2 import urlopen, HTTPError
    from urllib import urlencode

from .controller import OAuthResponseMiddleware
#from .provider import google

__all__ = ['OAuthClient', 'GoogleClient', 'AccessToken']

class AccessToken(dict):
    pass

class OAuthClient(object):
    """Client for :class:`Service`.

    :param service: service the client connects to
    :type service: :class:`Service`
    :param client_id: client id
    :type client_id: :class:`basestring`, :class:`numbers.Integral`
    :param client_secret: client secret key
    :type client_secret: :class:basestring`
    :param extra: additional arguments for authorization e.g.
                      ``scope='email,read_stream'``

    """

    #: (:class:`Service`) The service the client connects to.
    # service = google

    #: (:class:`basestring`) The client id.
    # client_id = None

    #: (:class:`basestring`) The client secret key.
    # client_secret = None

    #: (:class:`dict`) The additional arguments for authorization e.g.
    #: ``{'scope': 'email,read_stream'}``.

    def __init__(self, 
        client_service=None, 
        client_id=None, 
        client_secret=None,
        client_scope="email, read_stream",
        client_redirect_url='/oauth2callback',
        client_token=None,
        client_token_secret=None
        ):
        self.service = client_service
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = client_scope
        self.redirect_url = client_redirect_url
        self.token = {self.service.authorize_endpoint: self.client_secret}
        self.request_token = self.client_secret
        self.request_token_secret = client_token_secret
    def make_authorize_url(self, redirect_uri, state=None):
        """Makes an authorize URL.

        :param redirect_uri: callback url
        :type redirect_uri: :class:`basestring`
        :param state: optional state to get when the user returns to
                      callback
        :type state: :class:`basestring`
        :returns: generated authorize url
        :rtype: :class:`basestring`

        """
        query = dict(self.token)
        query.update(#consumer_key=self.client_id,
                     oauth_callback=redirect_uri,
                     #consumer_secret=self.client_secret,
                     #response_type='code',
                     #scope=self.scope
                     )
        if state is not None:
            query['state'] = state
        return '{0}?{1}'.format(self.service.authorize_endpoint,
                                urlencode(query))

    def load_username(self, access_token):
        """Load a username from the configured service suitable for the
        REMOTE_USER variable. A valid :class:`AccessToken` is provided to allow
        access to authenticated resources provided by the service. For GitHub
        the 'login' variable is used.

        :param access_token: a valid :class:`AccessToken`

        .. versionadded:: 0.1.2

        """
        self.request_token = access_token
        self.service.load_username(access_token, self.client_secret)

    def is_user_allowed(self, access_token):
        return self.service.is_user_allowed(access_token)

    def request_access_token(self, redirect_uri, client_token, client_token_secret, code):
        """Requests an access token.

        :param redirect_uri: ``redirect_uri`` that was passed to
                             :meth:`make_authorize_url`
        :type redirect_uri: :class:`basestring`
        :param code: verification code that authorize endpoint provides
        :type code: :class:`code`
        :returns: access token and additional data
        :rtype: :class:`AccessToken`

        """
        #log.debug("access token: %s" % self.access_token)
        
        form = {
        'oauth_consumer_key': self.client_id,
        'oauth_consumer_secret': self.client_secret,
        'oauth_callback': redirect_uri,
        'oauth_token': self.request_token,
        'oauth_token_secret' : self.request_token_secret}
        #log.debug(form)        
        u = requests.get(self.service.authorize_endpoint, 
            bytes(urlencode(form), 'utf8'))
        content_type = u.headers['Content-Type']
        if u.ok:
            return AccessToken(u.json())
        return AccessToken({})

    #def wsgi_middleware(self, *args, **kwargs):
    #    from .controller import OAuthResponseMiddleware
    #    return OAuthResponseMiddleware(*args, **kwargs)

class GoogleClient(OAuthClient):
    pass

