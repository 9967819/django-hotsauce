#!/usr/bin/env python
import tweepy

class TwitterClient(object):
    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret, 'http://localhost:8133/oauthcallback2')
                
        
        #self.session = {'twitter.oauth.request_token' : self.auth.request_token['oauth_token']}

