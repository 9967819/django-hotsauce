#!/usr/bin/env python

from djangohotsauce.utils.wsgilib import HTTPRequest
from djangohotsauce.utils.django_compat import get_resolver
from djangohotsauce.utils.django_compat import NoReverseMatch

def get_django_callable(request, urlconf):
    # Resolve the path (endpoint) to a view using legacy Django URL
    # resolver.
    resolver = get_resolver(urlconf)
    #Match the location to a view or callable
    (callback, args, kwargs) = resolver.resolve(request.path_url)
    # Create the wsgi ``response`` object.
    response = callback(request, *args, **kwargs)
    #if isinstance(response, HTTPRequest):
    #    #redirect
    #    path = response.environ['Location']
    #    response = self.error(response, 302, path)
    return response

    
