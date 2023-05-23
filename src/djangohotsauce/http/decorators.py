#!/usr/bin/env python
"""Common decorators for integration in generic views."""

from functools import wraps
from djangohotsauce.utils.wsgilib import HTTPForbiddenResponse, HTTPResponse

def post_required(view_func, **kwargs):
    @wraps(view_func)
    def _wrapper(*args, **kwargs):
        req = args[0]
        if (req.method != 'POST'):
            req.environ['wsgi.error'] = "please use POST"
            return HTTPForbiddenResponse("<p>Method not allowed.</p>", status=403, mimetype='text/html')
        return HTTPResponse("Hello world!")
    return _wrapper
