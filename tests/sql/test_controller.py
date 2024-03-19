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

class WSGIAppTestCase(WSGIControllerTestCase):

    def test_with_session(self):
        response = self.client.get('/test_with_session') # 
        self.assertEqual(response.status_code, '200 OK')

