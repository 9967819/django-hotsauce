#!/usr/bin/env python
# Copyright (c) Jack Bortone 2007-2009 <jack@isotopesoftware.ca>

from notmm.utils.wsgilib import HTTPRedirectResponse
from django.shortcuts import render_to_response

__all__ = ('handle302', 'handle303', 'handle404', 'handle500')

def handle302(request, **kwargs):
    location = kwargs['location']
    return HTTPRedirectResponse(location=location, status=302)

def handle303(request, **kwargs):
    location = kwargs['location']
    return HTTPRedirectResponse(location=location, status=303)

def handle500(request, **kwargs):
    template_name = '500.mako'
    return render_to_response(request, template_name, status=500)
 
def handle404(request, **kwargs):
    #self.logger.info('Location=%r' % request.path_url)
    #self.logger.info('Client IP=%r' % request.remote_addr)
    template_name = '404.mako'
    return render_to_response(request, template_name, status=404)
    
