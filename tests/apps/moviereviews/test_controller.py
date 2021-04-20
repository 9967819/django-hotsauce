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

    def test_render_index(self):
        response = self.client.get('/') # 
        self.assertEqual(response[1], '200 OK')

    def test_post_required_with_schevo_db(self):
        #req = HTTPRequest({})
        response = self.client.post('/test_post', data={})
        print ''.join([item for item in response[0]])
        #self.assertEqual(isinstance(response, ResponseClass), True, type(response))
        self.assertEqual(response[1], '200 OK')

