#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2019 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.
"""Decorator functions to interact with Schevo databases"""

from functools import wraps

from djangohotsauce.controllers.schevo import DurusController
from djangohotsauce.controllers.zodb import ZODBController


__all__ = ('with_schevo_database', 'with_durus_database')

def with_null_database(db_name='localhost', dbport=4545):
    """Do nothing decorator"""
    def decorator(view_func, **kwargs):
        @wraps(view_func, **kwargs)
        def _wrapper(req, *args, **kwargs):
            #req.environ[] = wsgi_app.db
            response = view_func(req, **kwargs)
            return response
        return _wrapper
    return decorator

def with_schevo_database(dbname='localhost', dbport=4545, 
    controller_class=ZODBController):
    """
    Decorator that adds a Schevo database object reference
    in the ``request.environ`` dictionary.

    """
    def decorator(view_func, **kwargs):
        @wraps(view_func, **kwargs)
        def _wrapper(req, *args, **kwargs):
            wsgi_app = controller_class(req, dbname)
            #if not wsgi_app.conn._db_is_open:
            #    print('opening db in decorator')
            #    wsgi_app.conn.safe_open_zodb(nethost)
            req.environ[wsgi_app.environ_key] = wsgi_app.db
            response = view_func(req, **kwargs)
            return response
        return _wrapper
    return decorator

def with_durus_database(dbname, controller_class=DurusController):
    return with_schevo_database(dbname, controller_class=controller_class)
