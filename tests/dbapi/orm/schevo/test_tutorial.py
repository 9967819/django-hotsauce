#!/usr/bin/env python

from test_support import unittest

# schevo
from schevo.database2 import Database 
from test_xdserver import XdserverProxy
#from model import ActorManager, MovieCastingManager, db
from model import db

class TutorialTestCase(unittest.TestCase):

    def setUp(self):
        super(TutorialTestCase, self).setUp()
        self.db = db

        # populate the database with sample data?
        # self.db.populate()

    def tearDown(self):
        #self.db.close()
        pass

    def runTest(self):
        pass

    def test_open_database(self):

        db = self.db
        #self.assertEqual(repr(db), "<Database u'Schevo Database' :: V 1>")
        
        # now lets make some introspection on db 
        self.assertEqual(isinstance(db, XdserverProxy), True, type(db))
        self.assertEqual(db.version, 1)
        self.assertEqual(db.format==2, True, db.format)

    #def test_find_keanu_reeves(self):
    #    import schevo.query as Q
    #    Person = ActorManager.objects.get(name=u"Keanu Reeves")
    #    #self.failUnlessEqual(isinstance(Person, db.Actor.__class__), True, type(Person))
    #    movie_list = MovieCastingManager.objects.find(actor=Person)
    #    self.assertEqual(isinstance(movie_list, Q.ResultsList), True)

