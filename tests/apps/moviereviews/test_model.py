import sys
#import mainapp
from notmm.utils.wsgilib import HTTPRequest
from test_support import (
    #WSGIControllerTestCase, 
    TestClient, 
    unittest,
    make_app,
    settings,
    ResponseClass
    )

from model import MessageManager
from apps.blogengine.test_tutorial import connection

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        

        self.db = MessageManager(connection).db_connection
        self.author = self.db.Author.findone(username="Jack Bortone")
        self.msg = MessageManager(connection,
            messageid="12300", 
            author=self.author, 
            content="test")

    def tearDown(self):
    #    self.db.close()
        pass

    #def test_populate(self):
    #    model.setup() 
    #    models = model.get_models()
    #    #print models

    def test_save(self):
        if self.msg.db_connection.conn._is_open:
            print "Database connection is open"
            try:
                self.msg.save(commit=False)
            except Exception, e:
                print "rollback() called"
                print e
                self.msg.db_connection.backend.rollback()

