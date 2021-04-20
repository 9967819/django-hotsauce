#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Database opener middleware for WSGI apps.

 Copyright (C) 2001-2007 Orbtech, L.L.C.

 libschevo - Another reimplementation of the Schevo DBMS.
 https://isotopesoftware.ca/software/libschevo/

 This toolkit is free software; you can redistribute it and/or
 modify it under the terms of the GNU Lesser General Public
 License as published by the Free Software Foundation; either
 version 2.1 of the License, or (at your option) any later version.

 This toolkit is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public
 License along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 For copyright, license, and warranty, see bottom of file.

"""
from djangohotsauce.controllers.wsgi import WSGIController

__all__ = ['SchevoController', 'DurusController']

class SchevoController(WSGIController):
    """Schevo Database connection middleware.

    A SchevoController instance will look for configuration items whose
    keys begin with ``schevo.db.``, and open the corresponding
    database using the location given by that configuration item.

    During WSGI application invocation, a SchevoController attaches
    those same keys in the WSGI environment, with the values being the
    open Schevo databases.  It also attaches a key ``schevo.db``,
    which is a dictionary whose keys are the names of each database and
    whose values are the open Schevo databases.

    The SchevoController instance itself is injected into the WSGI
    environment with the key ``schevo.dbopener``.  This allows other
    components in the WSGI stack to call the `open` and `close`
    methods to open and close more databases, respectively.
    """

    key_prefix = 'schevo.db.'
    backendClass = None

    def __init__(self, request, db_name, **kwargs):
        """Create a new ``SchevoController`` instance.

        request: The request to filter.

        if not 'backend' in kwargs:
            
        """
        
        super(SchevoController, self).__init__(**kwargs)
        if not 'backend' in kwargs:
            from djangohotsauce.dbapi.orm.schevo_compat import XdserverProxy
            self.backendClass = XdserverProxy
        else:
            self.backendClass = kwargs['backend']



        self.db_name = db_name
        self.environ_key = self.key_prefix + db_name
        self.setup_database(db_name)

        # Enable logging if debug is set
        #if (self.logger and self.debug):
        #    #self.logger.debug(repr(self))
        #    self.logger.debug("Configured schevo database: %s" % self.environ_key)

    def setup_database(self, db_name):
        # Adds a db instance to the current request object (self)
        self.db = self.backendClass(db_name)

    def __repr__(self):
        return "<SchevoController: %s>" % self.db_name

    def init_request(self, environ):
        super(SchevoController, self).init_request(environ)
        self.request.environ[self.environ_key] = self.db

class DurusController(SchevoController):
    pass
