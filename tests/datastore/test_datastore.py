import os
from test_support import unittest

from notmm.datastore import threadlocal

LocalStore = threadlocal.ThreadLocalStore

class ThreadLocalStoreTestCase(unittest.TestCase):
    
    def setUp(self):
        self.modname = os.environ.get('DJANGO_SETTINGS_MODULE', 'local_settings')
        self.storable = LocalStore(self.modname)

    def test_loads(self):
        # loads the objects by doing a __import__ 
        
        self.storable.loads()
        self.assertEqual(self.storable.initialized, True)
        self.assertEqual(hasattr(self.storable, 'DEBUG'), True)

    def test_count(self):
        # return the total amount of valid objects found
        # in self.storable. 
        self.storable = LocalStore(self.modname, autoload=True)
        settings_count = self.storable.count() 
        self.assertEqual(isinstance(settings_count, int), True)
    
    def test_clear(self):
        # for zeroing the settings found in __dict__...

        self.storable.clear()
        self.assertEqual(self.storable.count(), 0)
        #self.assertEqual(self.storable.initialized, False)

    def tearDown(self):
        pass
    def runTest(self):
        pass

