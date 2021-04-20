from wsgiref.headers import Headers as HeaderDict
from test_support import (
    unittest,
    ResponseClass,
    RequestClass,
    TestClient,
    WSGIController,
    WSGIControllerTestCase
    )

class HTTPResponseTestCase(WSGIControllerTestCase):
    charset = 'utf-8'
    mimetype = 'text/html'
    content = bytes()
    clientClass = TestClient

    def setUp(self):

        self.wsgi_app = ResponseClass(self.content, \
            mimetype=self.mimetype, charset=self.charset)
        
        #self.client = self.clientClass(self.callback)
 

class WSGIResponseTestCase(HTTPResponseTestCase):    
    def test_app_iter(self):
        response = self.wsgi_app
        self.assertEqual(len(response.content) == 0, True)
        self.assertEqual(len(response), 0)

    def test_write_unicode(self):
        # Python (2.5, 2.6, 2.7) specific test
        response = self.wsgi_app
        response.write(bytes('<p>hello, world!</p>'))
        self.assertEqual(response.content, str('<p>hello, world!</p>'))

    def test_format_status_int(self):    
        response = self.wsgi_app
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.status_code, '200 OK')
    
    def test_response_charset(self):  
        response = self.wsgi_app  
        self.assertEqual(response.charset==self.charset, True)

    def test_response_headers(self):
        response = self.wsgi_app
        self.assertEqual(isinstance(response.headers, list), True)

    def test_content_type(self):
        response = self.wsgi_app
        headers = HeaderDict(response.headers)
        content_type = headers['content-type']
        ct = response.content_type

        # Content-Type must match
        self.assertEqual(ct==content_type, True, ct)
        self.assertEqual(isinstance(ct, str), True, ct)
    
    def test_content_length(self):
        response = self.wsgi_app
        response.write(b'hello, world!')
        cl = response.content_length
        self.assertEqual(isinstance(cl, int), True, cl)
        self.assertEqual(int(cl), len(response.content), cl)
    
    def test_content_encoding(self):
        response = self.wsgi_app
        self.assertEqual(response.charset==self.charset, True, response.charset)

    #def test_get_response(self):
    #    response = self.client.get('/')
    #    self.assertEqual(response.status_int==200, True, response.status_int) 
