#!/usr/bin/env python
import logging
import json
import requests
import jwt
log = logging.getLogger(__name__)

class Service(object):
    """OAuth 2.0 service provider e.g. Facebook, Google. It takes
    endpoint urls for authorization and access token gathering APIs.

    :param authorize_endpoint: api url for authorization
    :type authorize_endpoint: :class:`basestring`
    :param access_token_endpoint: api url for getting access token
    :type access_token_endpoint: :class:`basestring`

    """

    #: (:class:`basestring`) The API URL for authorization.
    authorize_endpoint = None

    #: (:class:`basestring`) The API URL for getting access token.
    access_token_endpoint = None

    request_token_endpoint = None

    def __init__(self, authorize_endpoint, access_token_endpoint, 
        request_token_endpoint=None):
        def check_endpoint(endpoint):
            if not isinstance(endpoint, str):
                raise TypeError('endpoint must be a string, not ' +
                                repr(endpoint))
            elif not (endpoint.startswith('http://') or
                      endpoint.startswith('https://')):
                raise ValueError('endpoint must be a url string, not ' +
                                 repr(endpoint))
            return endpoint
        self.authorize_endpoint = check_endpoint(authorize_endpoint)
        self.access_token_endpoint = check_endpoint(access_token_endpoint)
        self.request_token_endpoint = check_endpoint(request_token_endpoint)

    def load_username(self, access_token, key):
        """Load a username from the service suitable for the REMOTE_USER
        variable. A valid :class:`AccessToken` is provided to allow access to
        authenticated resources provided by the service. If the service supports
        usernames this method must set the 'username' parameter to access_token.

        :param access_token: a valid :class:`AccessToken`

        .. versionadded:: 0.1.2

        """

        try:
            response = access_token.get(key)
        except:
            raise

        # Copy useful data
        user = dict(response)
        access_token["name"] = user["name"]
        access_token["email"] = user["email"]
        return access_token

    def is_user_allowed(self, access_token):
        """Check if the authenticated user is allowed to access the protected
        application. By default, any authenticated user is allowed access.
        Override this check to allow the :class:`Service` to further-restrict
        access based on additional information known by the service.

        :param access_token: a valid :class:`AccessToken`

        .. versionadded:: 0.1.3

        """
        return True

class GoogleService(Service):
    #authorize_endpoint='https://accounts.google.com/o/oauth2/auth',
    #access_token_endpoint='https://accounts.google.com/o/oauth2/token'
    pass
#google = GoogleService()

class TwitterService(Service):
    pass

twitter = TwitterService(
    authorize_endpoint='https://api.twitter.com/oauth/authorize',
    access_token_endpoint='https://api.twitter.com/oauth/access_token',
    request_token_endpoint='https://api.twitter.com/oauth/request_token'
    )
