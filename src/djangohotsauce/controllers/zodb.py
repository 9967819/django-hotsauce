#!/usr/bin/env python
# -*- coding: utf-8 -*-

from djangohotsauce.controllers.base import BaseController
from djangohotsauce.dbapi.orm import ClientStorageProxy
from djangohotsauce.utils.log import configure_logging

log = configure_logging('ZODBController')

__all__ = ['ZODBController']

class ZODBController(BaseController):

    schevo_key_prefix = 'schevo.db.'
    zodb_debug = True
    zodb_backend_class = ClientStorageProxy

    def __init__(self, request, db_name, **kwargs):
        super(ZODBController, self).__init__(**kwargs)
        self.environ_key = str(self.schevo_key_prefix + 'zodb')
        self.setup_database(db_name)
        
    def setup_database(self, db_name):
        self.backend = self.zodb_backend_class(db_name)
        #self.backend.safe_open_zodb(db_name)
        self.db = self.backend
    
    def init_request(self, environ):
        super(ZODBController, self).init_request(environ)
        if not self.environ_key in self.environ:
            self.environ[self.environ_key] = self.db
        return self
