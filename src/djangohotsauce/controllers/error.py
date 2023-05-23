#!/usr/bin/env python

from djangohotsauce.controllers.base import BaseController

__all__ = ['LoggingController']

class LoggingController(BaseController):
   
    #def registerWSGIHandlers(self, d):
    #    """Register appropriate wsgi callbacks (legacy method
    #    for backward compat only)"""
    #    for k, v in d:
    #        # "register" the callback function as a standard Django view
    #        # accessible by the controller extension
    #        self.sethandle(k, v)
    #    #self.registered = True
    #    return None

    def sethandle(self, name, string_or_callable):
        """Adds custom response handlers to a BaseController subclass.
        """
        # If string_or_callable is in the form of "foo.bar.quux",
        # the callable function should be the last part of the
        # string
        handler = None
        if isinstance(string_or_callable, str):
            if string_or_callable.find('.') != -1:
                bits = string_or_callable.rsplit('.', 1)
                m = __import__(bits[0], globals(), locals(), fromlist=[''])
                for component in bits[1:]:
                    if hasattr(m, component):
                        handler = getattr(m, component)
                        break
                    else:
                        #print 'debug: module %s has no such member: %r' % (m, component)
                        continue
        elif callable(string_or_callable):
            handler = string_or_callable
        else:
            raise ValueError("Unexpected string_or_callable type: %r" % \
                type(string_or_callable))

        if not callable(handler) and isinstance(handler, str):
            # Attempt to import it
            from djangohotsauce.utils.pastelib import import_func
            handler_obj = import_func(handler)
        else:
            handler_obj = handler

        # XXX Use staticmethod(func) here, because we want to support the
        # same positional arguments named by this callable
        setattr(self, name, handler_obj)

        return None
