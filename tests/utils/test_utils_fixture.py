import os
import yaml

from notmm.utils.YAMLFixture import YAMLFixture

from test_support import unittest

class YAMLFixtureTestCase(unittest.TestCase):
    
    def setUp(self):
        self.filename = os.path.join(os.getcwd(), 'lib/site-packages/sandbox/fixtures/initial_data.yaml')
        self.fixture = YAMLFixture(self.filename, schema_index_root='packages')
    
    def tearDown(self):
        self.fixture = None

    def test_schema_index_root(self):
        # full dump of initial_data (no index_root parameter specified)
        #self.fixture = YAMLFixture(self.filename)
        da = [item for item in self.fixture]
        db = self.fixture.dumps()
        self.assertEqual(da, db)

    def test_get(self):
        d1 = self.fixture.get(name='notmm')
        d2 = self.fixture.get(name='django.bugfixes')
        d3 = self.fixture.get(name='teatime')
        
        self.assertEqual(isinstance(d1, dict), True)
        self.assertEqual('name' in d1.keys(), True)

        self.assertEqual(d1 != d2, True, repr([d1, d2]))
        self.assertEqual(d1 != d3, True)
        self.assertEqual(d2 != d3, True)

        #print d1, d2, d3

    def test_filter(self):
        l1 = self.fixture.filter(category=u'Web Programming')
        self.assertEqual(isinstance(l1, list), True)
        l2 = self.fixture.filter(name="BlogEngine")

    
    def test_dumps(self):
        sample_data = self.fixture.dumps()
        self.assertEqual(isinstance(sample_data, list), True)
        self.assertEqual(len(sample_data) == 7, True, len(sample_data))

    def test_tojson(self):
        # encode the data to json
        json = self.fixture.tojson(strict=True)
        self.assertEqual(isinstance(json, basestring), True, type(json))

    def test_pathname(self):
        pathname = self.fixture.path
        self.assertEqual(os.path.exists(pathname), True)


