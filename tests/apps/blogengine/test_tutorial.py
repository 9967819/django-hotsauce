#!/usr/bin/env python

from test_support import unittest

# schevo
#from schevo.database2 import Database 
from notmm.dbapi.orm import ZODBFileStorageProxy
from model import AuthorManager, MessageManager


connection = ZODBFileStorageProxy('127.0.0.1:4343')

class TutorialTestCase(unittest.TestCase):

    def setUp(self):
        
        super(TutorialTestCase, self).setUp()
        self.db = MessageManager(connection).db_connection

        # populate the database with sample data?
        # self.db.populate()

    def tearDown(self):
        self.db.close()
    
    def test_open_database(self):

        db = self.db
        #self.assertEqual(repr(db), "<Database u'Schevo Database' :: V 25>")
        
        # now lets make some introspection on db 
        self.assertEqual(isinstance(db, ZODBFileStorageProxy), True, type(db))
        #self.assertEqual(db.version, 27) 
        self.assertEqual(db.format==2, True, db.format)

    def test_find_author(self):
        import schevo.query as Q
        Person = self.db.Author.findone(username=u"Jack Bortone")
        #self.failUnlessEqual(isinstance(Person, db.Actor.__class__), True, type(Person))
        blogentries = self.db.Message.find(author=Person)
        self.assertEqual(isinstance(blogentries, Q.ResultsList), True)
        #print blogentries
