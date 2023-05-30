#!/usr/bin/env python
"""Common HTTP utilities."""

from .httpserver import get_bind_addr, daemonize
from .decorators import post_required

