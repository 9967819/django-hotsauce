#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2007-2019 Jack Bortone <jack@isotopesoftware.ca>
All rights reserved.

This module allows communication with Schevo databases using 
the Durus 3.9 server backend.

Notes:

 1. As a minimum, You'll need the ``xdserver`` and the ``schevo``
 packages. 
 2. In addition, Durus 3.9 is being required.

"""

from schevo.backends.durus39 import XdserverBackend
from ._databaseproxy import DatabaseProxy

__all__ = ['XdserverProxy']

class XdserverProxy(DatabaseProxy):
    def __init__(self, db_name, **kwargs):
        # XXX Hack.
        if not 'db_connection_cls' in kwargs:
            kwargs['db_connection_cls'] = XdserverBackend
        super(XdserverProxy, self).__init__(db_name, **kwargs)

