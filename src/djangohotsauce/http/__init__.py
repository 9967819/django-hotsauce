#!/usr/bin/env python
# Copyright (C) 2007-2013 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved
"""Common HTTP utilities."""

from .httpserver import HTTPServer, get_bind_addr, daemonize
from .decorators import post_required

#from datetime import datetime
#def last_modified(timestamp):
#    "Returns the Last-Modified string since the epoc (see time.time)"
#    return str(datetime.fromtimestamp(timestamp))

