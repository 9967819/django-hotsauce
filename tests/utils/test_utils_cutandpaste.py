from test_support import unittest
import sys
import os
import time
import urllib
import logging

from notmm.utils.configparse import string_getter, int_getter

try:
    import termcolor
    _colored = termcolor.colored
except (ImportError, AttributeError):
    from django.utils.termcolors import colorize as _colored


class TermEventManager(object):

    fp = sys.stdout

    def _stdout(self, s):
        self.fp.write(str(s + os.linesep))

    def _colored(self, msg, **kwargs):
        """Write a string to the terminal with colored output"""
        _stdout(_colored(msg, **kwargs))

    def write(self, s, event_class='info'):
        emitter = self.system_event_types[event_class]
        emitter(s)

    system_event_types = {
        'info': lambda s: _colored(s, color='blue', attrs=['bold']),
        'debug': lambda s: _colored(s, color='white', attrs=['bold']),
        'warning': lambda s: _colored(s, color='orange', attrs=['bold'])
    }

RootEvent = TermEventManager()
RootEvent.write('system init')

class EventManagerTestCase(unittest.TestCase):
    def test_base(self):
        RootEvent.write('beauty is an artificial life', event_class="info")


