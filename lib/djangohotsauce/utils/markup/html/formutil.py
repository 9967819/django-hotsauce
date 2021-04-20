#!/usr/bin/env python
# Copyright (C) 2013 Jack Bortone
# All rights reserved.
"""Generic HTML form data extraction utilities"""

from urllib.parse import parse_qsl
from operator import itemgetter
#import threading

__all__ = ['FormWrapper', 'MultiDict']

class FormWrapper(dict):
    """A low-level extension to copy HTML form 
    data into a ``dict`` object."""
    
    def __init__(self, data={}):
        # FieldStorage assumes a default CONTENT_LENGTH of -1
        try:
            self.content_length = int(data.get('CONTENT_LENGTH', -1))    
        except ValueError:
            self.content_length = -1
        self.environ = data.copy()
    

class MultiDict(FormWrapper):

    def _get_raw_post_data(self, input_key='wsgi.input'):
        rfile = self.environ[input_key]
        # p = rfile.read(self.content_length)
        #    for k,v in parse_qsl(p, keep_blank_values=1):
        #        params[k.strip()] = str(v)
        if rfile is None:
            return dict()
        data = parse_qsl(rfile.read(
            int(self.content_length)
            ))
        return dict(map(itemgetter(0,1), data))

    raw_post_data = property(_get_raw_post_data)

