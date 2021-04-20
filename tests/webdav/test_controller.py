from threading import local
from functools import wraps
 
# support utilities
from test_support import (\
    unittest, 
    #setup_test_handlers,
    BaseControllerTestCase, 
    TestClient,
    make_app
    )

from notmm.controllers.wsgi import WSGIController
from notmm.utils.wsgilib import HTTPResponse

from controller import DAV10Controller

class DAV10Client(TestClient):
    pass

class DAV10ControllerTestCase(BaseControllerTestCase):

    wsgi_app = DAV10Controller # The wrapped HTTP/DAV wsgi handler
    
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
    
    def test_make_app(self):

        self.callback = make_app(self.wsgi_app)
        self.client = DAV10Client(self.callback)
 
        

