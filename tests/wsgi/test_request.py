import os, sys

from notmm.utils.configparse import is_string
from notmm.utils.django_compat import get_callable
from notmm.utils.wsgilib import HTTPRequest
from notmm.utils.markup import FormWrapper
from test_support import WSGIControllerTestCase

class HTTPRequestTestCase(WSGIControllerTestCase):

    def test_post_required(self):
        client = self.client
        response = client.post('/')


