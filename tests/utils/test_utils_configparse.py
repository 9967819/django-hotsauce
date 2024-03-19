#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007-2011 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.
#
# Please see the "LICENSE" and "NOTICE" files included in the source 
# distribution for details on licensing info.

from configobj import Section
from notmm.utils.configparse import *

from test_support import unittest

class UserConfigTestCase(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_loadconf(self):
        config = loadconf('development.ini')
        self.assertEqual(isinstance(config, dict), True)
        
        section = loadconf('development.ini', section='blogengine')
        self.assertEqual(isinstance(section, Section), True)

    def test_string_getter(self):
        app_conf = loadconf('development.ini') 
        s = string_getter(app_conf, 'blogengine', 'schevo.db.blogengine')
        self.assertEqual(isinstance(s, str), True, repr(s))

    def tearDown(self):
        pass

