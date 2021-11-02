#!/usr/bin/env python
# -*- coding: utf-8 -*-
from djangohotsauce.controllers.wsgi import WSGIController
from djangohotsauce.utils.log import configure_logging
import tweepy

log = configure_logging('OAuthController')

__all__ = ['TwitterController']

class TwitterController(WSGIController):

    OAuthHandler = tweepy.OAuthHandler

    def __init__(self,  **kwargs):
        super(TwitterController, self).__init__(**kwargs) 
        self.auth = self.OAuthHandler(self.settings.TWITTER_API_KEY,
                self.settings.TWITTER_API_SECRET_KEY)
        self.api = tweepy.API(self.auth)

        super(TwitterController, self).__init__(**kwargs)
    
    def init_request(self, request):
        request.environ['tweepy.api'] = self.api
        return request
