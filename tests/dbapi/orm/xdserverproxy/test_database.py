from notmm.dbapi.orm import XdserverProxy
from test_support import unittest
from datetime import datetime

class QuerySetTestCase(unittest.TestCase):
    # Test case to emulate Django QuerySets using Schevo databases under
    # the hood.

    db = None
    model = None

class EntryManagerTestCase(QuerySetTestCase):

    db = XdserverProxy('blogs')
    model = db.BlogEntry 

    def test_intersection(self):
        # test getting all entries
        Q = self.db.Q
        q1 = Q.Match(self.model, 'pub_date', '<=', datetime.today())
        q2 = Q.Match(self.model, 'reviewed', '==', True)
        results = Q.Intersection(q1, q2)
        self.assertEqual(isinstance(results, Q.Intersection), True)

