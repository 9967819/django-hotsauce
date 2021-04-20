#!/usr/bin/env python
#to create the database:
# schevo db create --app lib/site-packages/moviereviews zodb:///var/db/zodb/test.fs

from schevo import database
from ZEO import ClientStorage
from ZODB import DB
from test_support import unittest

class ClientStorageTestCase(unittest.TestCase):
    def setUp(self):
        #self.filename = 'zodb:///var/db/zodb/test.fs'
        self.addr = ('127.0.0.1', 4343)
    def test_open(self):
        self.storage = ClientStorage.ClientStorage(self.addr)
        self.zodb = DB(self.storage)
        self.conn = self.zodb.open()
        

class SchevoTestCase(unittest.TestCase):

    connected = False

    def setUp(self):
        self.dbname = 'zodb://127.0.0.1:4343'
        self.db = database.open(self.dbname)
    def tearDown(self):
        self.db.close()

    def test_open(self):
        #self.assertEqual(equivalent(db, db2), True)
        self.assertEqual(self.db != None, True)
    
    def test_extents(self):
        lst = self.db.extents()
        self.assertEqual(isinstance(lst, list), True) #print lst

    def test_populate(self):
        #self.db.populate()
        #print sorted(item for item in self.db.Message)
        pass
