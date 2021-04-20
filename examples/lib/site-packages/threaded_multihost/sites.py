# -*- coding: utf-8 -*-
"""Provides utilities to help multi-site aware applications.

:Authors:
    - Bruce Kroeze
"""
"""
New BSD License
===============
Copyright (c) 2008, Bruce Kroeze http://coderseye.com

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of SolidSiteSolutions LLC, Zefamily LLC nor the names of its 
      contributors may be used to endorse or promote products derived from this 
      software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__docformat__="restructuredtext"

from threaded_multihost import threadlocals
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.loading import app_cache_ready
import keyedcache
import logging

log = logging.getLogger('threaded_multihost.sites')
_WARNED = {}

class MultihostNotReady(Exception):
    pass

def by_host(host=None, id_only=False):
    """Get the current site by looking at the request stored in the thread.  
    
    Returns the best match found in the `django.contrib.sites` app.  If not
    found, then returns the default set as given in `settings.SITE_ID`
    
    Params:
     - `host`: optional, host to look up
     - `id_only`: if true, then do not retrieve the full site, just the id.
    """
    global _WARNED
    if id_only:
        site = -1
    else:
        site = None
        
    debug_domain = None
    if settings.DEBUG and hasattr(settings, 'MULTIHOST_DEBUG_DOMAIN'):
        raw = settings.MULTIHOST_DEBUG_DOMAIN
        parts = raw.split('=')
        if len(parts) == 2:
            debug_domain = parts[0]
            debug_target = parts[1]
        else:
            debug_domain = raw
            debug_target = 'com'

    if not host:
        request = threadlocals.get_current_request()
        if request:
            host = request.get_host()
        else:
            log.debug('No request')
            site = by_settings(id_only=id_only)
        
    if host:
        if app_cache_ready():
            try:
                site = keyedcache.cache_get('SITE', host=host, id_only=id_only)
            except keyedcache.NotCachedError, nce:
                try:
                    log.debug('looking up site by host: %s', host)
                    site = Site.objects.get(domain=host)
                except Site.DoesNotExist:
                    if host.find(":") > -1:
                        try:
                            # strip the port
                            host = host.split(":")[0]
                            site = Site.objects.get(domain=host)
                        except Site.DoesNotExist:
                            pass
                    if debug_domain and host.endswith(debug_domain):
                        host = host[:-len(debug_domain)] + debug_target
                        log.debug('Using debug domain: %s', host)
                        try:
                            site = Site.objects.get(domain=host)
                        except Site.DoesNotExist:
                            pass

                if site:
                    keyedcache.cache_set(nce.key, value=site)
                    
                    if id_only:
                        site = site.id
                    
                else:
                    if not host in _WARNED:
                        log.warn("Site for '%s' is not configured on this site - add to sites in admin", host)
                        _WARNED[host] = True
                        
                    site = by_settings(id_only=id_only)
                
        else:
            log.debug('app cache not ready')
            site = by_settings(id_only=id_only)
    else:
        pass
        #log.debug('no host')    
            
    # if site is None or site == -1:
    #     raise MultihostNotReady()
            
    #log.debug("current site: %s", site)
    return site
        
def by_request(request=None, id_only=False):
    """Look up a site given an explicit request rather than using the request
    currently in the `threadlocals`.
    
    Params:
     - `request`: optional, the request to use, defaults to the request found in the threadlocals
     - `id_only`: if true, then only the id is returned.
    """
    host = None
    if request and 'HTTP_HOST' in request.META:
        host = request.META['HTTP_HOST']
    return by_host(host=host, id_only=id_only)
        
def by_settings(id_only=False):
    """Get the site according to the SITE_ID in settings.
    
    Params:
     - `id_only`: if true, then only the id is returned.
    """
    #log.debug('from_settings')
    global _WARNED
    if id_only:
        return settings.SITE_ID
        
    try:
        return Site.objects.get(pk=settings.SITE_ID)
    except Exception, e:
        message = e.args[0]
        if message.find("django_site") > 0:
            site = None
            if not 'django_site' in _WARNED:
                log.warn("Error, couldn't find django_site in database, ok if you are in syncdb")
                _WARNED['django_site'] = True
        else:
            raise
            
    return site
