#!/usr/bin/env python
# -*- coding: utf-8 -*-
from djangohotsauce.controllers.wsgi import WSGIController, sessionmanager, get_current_request
from djangohotsauce.utils.log import configure_logging
from djangohotsauce.utils.wsgilib import HTTPRedirectResponse
import tweepy
                
log = configure_logging('OAuthController')

from djangohotsauce.http.oauthclient import (
     OAuthClient,
     OAuthResponseMiddleware,
     )

__all__ = ['OAuthController', 'oauthclient']

class OAuthController(WSGIController):
    def __init__(self,  client, **kwargs):
        self.client = client
        super(OAuthController, self).__init__(**kwargs)
    
    #def init_request(self, environ):
    #    self._request = self._request_class(environ)
    #    return self._request

    def __call__(self, environ, start_response):

        path_url = environ['PATH_INFO']
        if '/oauthcallback2' in path_url:
            try:
                self.redirect_url = self.client.auth.get_authorization_url()
            except tweepy.TweepError:
                raise Exception("Error fetching request token.")

            if not 'oauth_token' in self.environ:
                # redirect to authorization url 
                url_to = self.client.redirect_url
                return HTTPRedirectResponse(url_to)(environ, start_response)
            
            if 'oauth_token' and 'oauth_verifier' in self.request.GET:
                token = self.request.GET['oauth_token']
                verifier = self.request.GET['oauth_verifier']
                self.client.auth.request_token = {
                    'oauth_token': token,
                    'oauth_token_secret': verifier}
                self.request.environ['twitter.access_token'] = self.client.auth.get_accesss_token(verifier)    
        return super(OAuthController, self).__call__(environ, start_response)


oauthclient = OAuthClient
