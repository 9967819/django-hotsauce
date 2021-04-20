#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import demjson
import test_response
from notmm.utils.wsgilib import HTTPResponse as BaseHTTPResponse

ResponseClass = BaseHTTPResponse

class JSONResponseTestCase(test_response.HTTPResponseTestCase):
    
    mimetype = 'application/json'
    charset = 'utf-8'
    
    def setUp(self):
        self.wsgi_app = ResponseClass(
            demjson.encode({'key':'value'}),
            mimetype=self.mimetype,
            charset=self.charset)
    
    def test_write(self):
        pass

