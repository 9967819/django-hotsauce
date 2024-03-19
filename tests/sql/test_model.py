import sys
#import mainapp
from notmm.utils.wsgilib import HTTPRequest
from test_support import (
    WSGIControllerTestCase, 
    TestClient, 
    unittest,
    make_app,
    settings,
    ResponseClass
    )

class MessageTestCase(WSGIControllerTestCase):
    def test_create_message(self):
        pass

