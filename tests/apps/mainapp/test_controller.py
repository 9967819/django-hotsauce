import sys

from test_support import WSGIControllerTestCase

class WSGIAppTestCase(WSGIControllerTestCase):

    def test_render_index(self):
        response = self.client.get('/') # /blog/ 
        self.assertEqual(response[1], '200 OK')

