#!/usr/bin/env python
"""Common HTTP utilities."""

from .httpserver import daemonize
from .decorators import post_required

def main(wsgi_app):
    return daemonize(wsgi_app, ('127.0.0.1', '8000'))
