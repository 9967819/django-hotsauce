#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Decorators functions returning a callable"""

from functools import wraps
from session import ScopedSession

__all__ = ('with_session',)

def with_session(engine=None):
    """
    Decorator function for attaching a `` Session`` instance
    as a keyword argument in ``request.environ``. 
    """
    def decorator(view_func):
        def _wrapper(request, *args, **kwargs):
            if engine is not None:
                #print "setting session"
                Session = ScopedSession(engine=engine)
                #Session.set_session(engine)
                request.environ['_scoped_session'] = Session.get_session()
            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapper)
    return decorator

