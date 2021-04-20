# -*- coding: utf-8 -*-
""" threadlocals Middleware, provides a better, faster way to get at request and user.

:Authors:
   - Herbert Poul http://sct.sphene.net
   - Bruce Kroeze

Branched from [http://code.djangoproject.com/wiki/CookBookthreadlocalsAndUser CookBookThreadLocalsAndUser]
as modified by [http://sct.sphene.net Sphene Community tools].
"""

from threaded_multihost.threadlocals import set_thread_variable, set_current_user

class ThreadLocalMiddleware(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""

    def process_request(self, request):
        set_thread_variable('request', request)
        set_current_user(request.user)
        