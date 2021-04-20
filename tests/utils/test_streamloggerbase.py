#from notmm.utils.cutandpaste import *
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

class StreamLoggerBase(object):

    fp = sys.stderr

    def _stdout(self, s):
        self.fp.write(str(s + os.linesep))

    def _colored(self, msg, **kwargs):
        """Write a string to the terminal with colored output"""
        _stdout(_colored(msg, **kwargs))

    def write(self, s, event_class='info'):
        emitter = self._system_event_types[event_class]
        self._stdout(emitter(s))

    _system_event_types = {
        'info': lambda s: _colored(s, color='blue', attrs=('bold',)),
        'debug': lambda s: _colored(s, color='white', attrs=('bold',)),
        'warning': lambda s: _colored(s, color='orange', attrs=('bold',))
    }


class StreamLoggerBaseTest(unittest.TestCase):
    
    def test_emit_log_record_to_stdout(self):
        # logger = StreamLoggerBase()
        # logger.write('beauty is an artificial life', event_class="info")
        pass

