#!/usr/bin/env python
# -*- coding: utf-8 -*-

from schevo.backends.zodb import ZodbBackend # require zodb 3.7.4
from ._databaseproxy import DatabaseProxy

__all__ = ('ClientStorageProxy',)

class ClientStorageProxy(DatabaseProxy):
    db_backend = ZodbBackend
    
    #def __getattr__(self, attr):
    #    try:
    #        return getattr(self.conn, attr)
    #    except AttributeError:
    #        raise 

