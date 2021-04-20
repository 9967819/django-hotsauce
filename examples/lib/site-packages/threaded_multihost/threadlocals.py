# -*- coding: utf-8 -*-
"""__init__ module for the threadlocals package

:Authors:
    - Herbert Poul http://sct.sphene.net
    - Bruce Kroeze http://gosatchmo.com
"""
"""
New BSD License
===============
Copyright (c) 2008, Bruce Kroeze http://solidsitesolutions.com

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

import logging

log = logging.getLogger('ThreadLocalMiddleware')

try:
    from threading import local
except ImportError:
    log.warn('getting threadlocal support from django')
    from django.utils._threading_local import local
    
from django.contrib.sites.models import Site

_threadlocals = local()

def get_current_host(request = None):
    if not request:
        request = get_current_request()
    if request:
        try:
            host = request.META["HTTP_HOST"]
            return host
        except KeyError:
            pass
    #log.warn('No request found - returning default site')
    site = Site.objects.get_current()
    return site.domain

def get_current_request():
    return get_thread_variable('request', None)

def get_current_session():
    req = get_current_request()
    if req == None: return None
    return req.session
    
def get_current_user():
    user = get_thread_variable('user', None)
    if user != None: return user
    req = get_current_request()
    if req == None: return None
    return req.user

def set_current_user(user):
    set_thread_variable('user', user)

def set_thread_variable(key, var):
    setattr(_threadlocals, key, var)
    
def get_thread_variable(key, default=None):
    return getattr(_threadlocals, key, default)