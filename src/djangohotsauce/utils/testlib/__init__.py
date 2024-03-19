#!/usr/bin/env python
"""
djangohotsauce.utils.testlib - Test utilities for enhanced unittest integration
in Python.

Description
===========

This module supports recursive packages loading and testing with
unittest module. Require Python 2.7.3+. Untested with Python 3.x.

Usage
=====

Run test scripts in package ``foo``:

 % run.py -C ``foo``

Basic configuration
===================

In your development.ini, add a section name "testrunner" like so:

 [testrunner]

 collections=foo bar

Then run the following:

 % mkdir -p {foo,bar}/__init__.py

Launch the test runner with:

 % ./run.py -C foo bar 

Examples
========

See ``tests/run.py`` for a example test runner script.

"""

from .collection2 import (
    TestCollection, get_test_modules, CollectionError)
from .base import SimpleTestRunner

__all__ = ('collection2', 'base', 'TestCollection', 'get_test_modules',
    'CollectionError', 'SimpleTestRunner')

#
