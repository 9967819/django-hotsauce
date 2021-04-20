#!/usr/bin/env python
# Copyright (c) Jack Bortone 2007-2009 <robillard.etienne@gmail.com>

from notmm.utils.wsgilib import HTTPRedirectResponse
from notmm.utils.template import direct_to_template

__all__ = ('handle302', 'handle404', 'handle500')

def handle302(request, **kwargs):
    location = kwargs.get('location', '/')
    return HTTPRedirectResponse(location=location)

def handle500(request, template_name='500.mako'):
    return direct_to_template(request, template_name, status=500)
 
def handle404(request, template_name='404.mako'):
    return direct_to_template(request, template_name, status=404)
    
