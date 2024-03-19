#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import os
#import traceback
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from notmm.controllers.wsgi             import BaseController, WSGIController
from notmm.utils.django_settings        import SettingsProxy
from notmm.utils.wsgilib                import HTTPRequest, HTTPResponse
from notmm.utils.django_compat          import RegexURLResolver, get_resolver

settings = SettingsProxy(autoload=True).settings
class RegexUrlResolverTestCase(unittest.TestCase):
    
    def setUp(self):
        self.resolver_func = get_resolver
        self.urlconf = settings.ROOT_URLCONF
    def test_get_resolver(self):
        result = self.resolver_func(self.urlconf)
        self.failIfEqual(result, None)

if __name__ == '__main__':
    unittest.main()
