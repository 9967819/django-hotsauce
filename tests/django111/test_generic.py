#!/usr/bin/env python
# This test suite verifies the environment for common misconfiguration
# problems.

import os, sys

from notmm.utils.configparse import is_string
from notmm.utils.django_compat import get_callable
from notmm.utils.wsgilib import HTTPRequest

from test_support import unittest

class SanityCheckTestCase(unittest.TestCase):

    def test_get_callable(self):
        #Convert a string version of a function name to the callable object.
        #If the lookup_view is not an import path, it is assumed to be a URL pattern
        #label and the original string is returned.
        #If can_fail is True, lookup_view might be a URL pattern label, so errors
        #during the import fail and the string is returned.
        lookup_view = get_callable('moviereviews.views.test_schevo_database')

        # lookup_view must be a callable
        self.assertEqual('__call__' in dir(lookup_view), True)
        
        # The name of the function should match the view name
        self.assertEqual(lookup_view.__name__ is 'test_schevo_database', True)

    def test_django_home(self):
        # Detection of DJANGO_HOME in $ENV. DJANGO_HOME must
        # be set and the ``django`` package must be importable
        # from this directory.

        keyname = 'DJANGO_HOME'

        have_django_home = bool(is_string(os.environ.get(keyname, '')))
        self.assertEqual(have_django_home, True)

        # if we get here then we can use a shortcut..
        django_home = os.environ[keyname]

        # Check if the django_home path exists..
        self.assertEqual(os.path.exists(django_home), True, """\
Whoa there! Your DJANGO_HOME setting is invalid. Please verify if the path exists and run the test again.
No such path: %s""" % django_home) 

        # And if the ``django`` package can be imported from that
        # specified location...
        self.assertEqual(sys.path.__contains__(django_home), True, """\
Your PYTHONPATH setting seems invalid. It should contains %s.""" % keyname)

        #mod = __import__('django', globals(), locals(), fromlist=[''])
        #basedir = os.path.realpath(getattr(mod, '__file__').split('/')[:-1])
        #self.assertEqual(basedir==DJANGO_HOME, 'basedir: %s' % basedir)
        
    def test_django_settings_module(self):
        # DJANGO_SETTINGS_MODULE must be importable
        try:
            settings_module = __import__(os.environ['DJANGO_SETTINGS_MODULE'], {}, {}, fromlist=[''])
        except ImportError:
            # this is for backward-compatibility reasons..
            self.fail("""\
%s is not doing currently anything.
Hint: Your PYTHONPATH is probably wrong and/or out-of-date.""" %
SETTINGS_MODULE_NAME)
    
    def test_django_request_context(self):
        # For this to work RequestContext must be
        # a subclass of a dictionary type !
        from django.template import RequestContext, Context
        self.failUnlessEqual(issubclass(RequestContext, Context), True) 

