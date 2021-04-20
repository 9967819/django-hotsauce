#!/usr/bin/env python
#from schevo.database2 import Database
from schevo.database import format_dbclass, equivalent
from test_support import unittest
from notmm.dbapi.orm import ClientStorageProxy

class ClientStorageTestCase(unittest.TestCase):

    connected = False

    def setUp(self):
        self.dbname = '127.0.0.1:4343'
        ClientStorageProxy.cache.clear()

    def tearDown(self):
        pass

    def test_initdb(self):
        db = ClientStorageProxy(self.dbname)
        #db.initdb(db.conn)
        #db2 = ZODBFileStorageProxy(self.dbname)
        #self.assertEqual(equivalent(db, db2), True)
        self.assertEqual(db != None, True)

        print db.extents()
