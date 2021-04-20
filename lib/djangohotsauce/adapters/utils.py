#!/usr/bin/env python
# -*- coding: utf-8 -*-
#DEPRECATED: 1.2
from djangohotsauce.controllers.wsgi import WSGIController
from djangohotsauce.utils.log import configure_logging
#oauthclient
from djangohotsauce.controllers.oauth import OAuthController
from djangohotsauce.http.oauthclient import client
from djangohotsauce.http.oauthclient.provider import google

log = configure_logging(__name__)

__all__ = ['make_app']

def make_app(settings, enable_oauth=True, enable_logging=True):
    wsgi_app = WSGIController(settings=settings)
    if enable_oauth:
            #google_client = client.GoogleClient(
            #settings.OAUTH2_CLIENT_ID,
            #access_token=settings.OAUTH2_ACCESS_TOKEN,
            #scope=settings.OAUTH2_SCOPE, 
            #redirect_url=settings.OAUTH2_REDIRECT_URL)
        oauthclient = client.GoogleClient(
            google, 
            settings.OAUTH2_CLIENT_ID,
            settings.OAUTH2_ACCESS_TOKEN,
            settings.OAUTH2_SCOPE,
            settings.OAUTH2_REDIRECT_URL
            )
        wsgi_app = OAuthController(wsgi_app, oauthclient)
        log.debug("Generic OAUTH2 support enabled.")
    return wsgi_app

