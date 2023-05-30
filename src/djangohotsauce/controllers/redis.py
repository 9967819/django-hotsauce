#!/usr/bin/env python
# -*- coding: utf-8 -*-
from djangohotsauce.controllers.wsgi import WSGIController, sessionmanager, get_current_request
from djangohotsauce.utils.log import configure_logging
import redis        
log = configure_logging('RedisController')

__all__ = ['RedisController']

class RedisController(WSGIController):
    """Base RedisController class.

    Routes configured paths to redis backend. 
    
    Important: In case the path does not exists, 
    returns the main wsgi app and create 
    a key in redis.
    """

    def __init__(self, host='localhost', port=6379, db=0):
        self.server = redis.Redis(host=host, port=port, db=db)
        super(RedisController, self).__init__(**kwargs)
    
    #def init_request(self, environ):
    #    self._request = self._request_class(environ)
    #    return self._request

    def __call__(self, environ, start_response):
    
        return super(RedisController, self).__call__(environ, start_response)

