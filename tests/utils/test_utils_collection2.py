#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Test suite for the ``notmm.utils.testlib`` package.
# 
import os
import re
import sys

from notmm.utils.configparse import loadconf, string_getter
from notmm.utils.testlib import *

from test_support import unittest

class TestCollectionTestCase(unittest.TestCase):
    
    app_conf = loadconf('development.ini')
        
    def setUp(self):
        self.loader = TestCollection()

    def test_load_tests_from_names(self):
        
        #XXX inexistent packages should raises CollectionError :)
        self.assertRaises(ImportError, \
            self.loader.loadTestsFromList, ('werkzeug'))

    #def test_get_base_dir(self):
    #    from notmm.utils.testlib.collection2 import get_base_dir
    #    self.assertEqual(get_base_dir('apps/authkit'), 'apps/authkit')

    def test_find_all_unique_test_cases(self):
        # XXX ``TestCollection.findTestCases`` must be able to load
        # test cases from different files while having the same
        # file name...
        method = 'findTestCases'
        self.assertEqual(hasattr(self.loader, method), True)
        testSuite = self.loader.loadTestsFromNames(
            'apps/blogengine'
            )
        self.assertEqual(isinstance(testSuite, \
            unittest.TestSuite), True)
