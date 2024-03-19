import sys
#import mainapp
from notmm.controllers.wsgi import WSGIController
from notmm.controllers.auth import LoginController
from notmm.utils.wsgilib import HTTPRequest
from notmm.utils.configparse import loadconf

auth_conf = loadconf('development.ini', section='authkit')

from test_support import (
    WSGIControllerTestCase, 
    TestClient, 
    unittest,
    make_app,
    settings
    )

class AuthkitControllerTestCase(WSGIControllerTestCase):

    wsgi_app = WSGIController

    def setUp(self):
        self.test_init_middleware()
        self.client = TestClient(self.callback)

    def test_init_middleware(self):
        
        self.callback = LoginController(self.wsgi_app, auth_conf=auth_conf)
    

    def test_session_login(self):
        response = self.client.get('/session_login/') # 
        self.assertEqual(response[1], '200 OK')

    def test_session_login_POST(self):
        # XXX authenticate_user method test
        postdata = {
            'username': 'guest',
            'password': 'guest'}
        
        #client = TestClient(self.callback, method="POST")
        response = self.client.post('/session_login/', postdata)
        #req = HTTPRequest(environ=self.client.environ.copy())
        #self.assertEqual(req.method, 'POST')
        
        self.assertEqual(response[1], '200 OK')
        #self.assertEqual('REMOTE_USER' in response.environ, True)

