#!/usr/bin/env python
"""This module allows communication with Schevo named
databases using the Durus Extended Server.

You'll need the ``xdserver`` package and the ``schevodurus``
packages. In addition, a minimal version of Schevo 3.1 is
also required.

Test case is in ``dbapi/schevo/test_xdserver.py``.
"""

# Copyright (c) 2010 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.

#from schevodurus.backend import DurusBackend as Connection
#from durus.connection import Connection
#from durus.btree import BTree
from schevo.backends.durus39 import DurusBackend as Connection
from schevo.database import format_dbclass, equivalent
from schevo import icon
import schevo.mt
from test_support import unittest
from notmm.dbapi.orm import XdserverProxy

class XdserverProxyTestCase(unittest.TestCase):

    connected = False

    def setUp(self):
        self.dbname = 'moviereviews'

    def tearDown(self):
        pass

    def test_equivalent(self):
        db = XdserverProxy(self.dbname)
        db2 = XdserverProxy(self.dbname)
        self.assertEqual(equivalent(db, db2), True)
        #db.close()
        #db2.close()
