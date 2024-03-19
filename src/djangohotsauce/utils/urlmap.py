#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A class-based URL resolving module for Django.

* RegexURLMap:
    Provides a easy-to-use API to build logical groups of callbacks 
    to URIs.
* RegexURLMapException: 
    Reserved for future uses; Exception handling of ``RegexURLMap`` instances.
* include, patterns, and url functions are provided as helpers while upgrading from Django to RegexURLMap.

"""

from importlib import import_module
import re, logging

from .django_compat import RegexURLPattern, RegexURLResolver

log = logging.getLogger(__name__)

__all__ = ['RegexURLMapException', 'RegexURLMap', 'url', 'include', 'patterns']

include = lambda urlconf: [urlconf]

def patterns(prefix, *args):
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = url(prefix=prefix, *t)
        elif isinstance(t, RegexURLPattern):
            t.add_prefix(prefix)
        pattern_list.append(t)
    return pattern_list

def url(regex, view, kwargs={}, name=None, namespace=None, prefix=''):
    if isinstance(view, (tuple, list)):
        # For include(...) processing.
        return RegexURLResolver(regex, view[0], kwargs, namespace=namespace)
    else:
        if isinstance(view, str):
            if not view:
                raise RegexURLMapException('Empty URL pattern view name not permitted (for pattern %r)' % regex)
            if prefix:
                view = prefix + '.' + view
        return RegexURLPattern(regex, view, kwargs, name=name)

class RegexURLMapException(Exception):
    """
    Generic error manipulating a ``RegexURLMap`` object.
    
    """

class RegexURLMap(object):
    """
    Add or create a list of available ``RegexURLPattern`` instances.
 
    Usage ::

    .. coding: python

        >>> from djangohotsauce.controllers.routing import RegexURLMap
        >>> urlpatterns = RegexURLMap(label='default')
        >>> print repr(urlpatterns)
        <RegexURLMap: 'default'> 
        >>> urlpatterns.add_routes('myapp.views', ...) # default
        >>> urlpatterns.include(foo.bar.urls) # include urls from another module
    """

    def __init__(self, label='yadayada', verbosity=1):
        self.routes = []
        self.label = label # Label for this urlmap object
        self.debug = (verbosity >= 2)
        self.namespace = label
    
    def __len__(self):
        # Return the number of routes available for this urlmapper
        return len(self.routes)

    def __repr__(self):
        return "<RegexURLMap: %r>" % self.label
    
    def add_routes(self, callback_prefix='', *args):
        """
        Adds a sequence of ``RegexURLPattern`` instances for routing
        valid HTTP requests to a WSGI callback function.

        Unlike the original ``include`` hook provided in Django, this 
        method can be used to create logical groups of routes within the
        same urls.py file. 
        
        """
        self.callback_prefix = callback_prefix
        
        for t in args:
            if hasattr(t, 'name'):
                self.makeroute(t, app_label=t.name)
            else:
                self.makeroute(t)

    def makeroute(self, t, app_label=None):
        """Connect a wsgi app to a URI. Invoked by ``add_routes`` to
        flattenize all urls.py into a immutable list of URIs."""
        route = None
        if app_label and self.debug:
            log.debug("New route: %s" % app_label)
            
        if isinstance(t, (list, tuple)):
            #assert len(t) >= 2, t

            if len(t) == 2:
                regex, view = t
                kwargs = {}
            elif len(t) == 3:
                regex, view, kwargs = t
            elif len(t) == 4:
                regex, view, kwargs, app_label = t
            else:
                #not implemented
                raise
            route = url(regex, view, kwargs=kwargs, name=app_label, 
                prefix=self.callback_prefix, namespace=self.namespace)
            #assert isinstance(route, RegexURLPattern), type(route)

        elif isinstance(t, RegexURLPattern):
            if app_label is not None:
                assert (t.name == app_label), (t.name, app_label)
            #    #t.name = app_label
                if self.debug:
                    log.debug("Registering view: %s" % t.name)
                    if hasattr(t, '_callback_str'):
                        log.debug("callback_str: %s" % t._callback_str)
            route = t
        elif isinstance(t, RegexURLResolver):
            for route in t.url_patterns:
                #log.debug("Found new route: %s" % route)
                route.add_prefix(self.callback_prefix)
                self.routes.append(route)
            #route.namespace = self.namespace
            #    raise RegexURLMapException("app_label is required here!")
            #if app_label is not None:
            #    log.debug("Setting route name to %s" % self.label)
            #    route.app_name = app_label
        else:
            log.debug("Discarding route: %s" % t)

        if isinstance(route, RegexURLPattern):
            route.add_prefix(self.callback_prefix)
            #assert (route.name == app_label), route.name
        try:
            self.routes.append(route)
        except AttributeError as e:
            raise RegexURLMapException(e)


    def include(self, urlobj, prefix='', callback_prefix='',
        attr_name='urlpatterns', app_label=None):
        """Includes urls found in module ``urlobj``.
        
        """
        #objtype = type(urlobj)
        if isinstance(urlobj, tuple):
            urls = urlobj[0] # handle admin.site.urls
        #elif objtype in (str, basestring):
        else:
            urlconf = import_module(urlobj)
            #log.debug("urlconf=%r"%urlconf)
            urls = getattr(urlconf, attr_name)
        #else:
        #    # not a string type, neither a sequence, so its the default
        #    # behavior (urlconf)
        #    try:
        #        urls = getattr(urlobj, attr_name)
        #    except AttributeError:
        #        #assert attr_name in urlobj.__dict__, 'Not a valid urls.py file.'
        #        raise RegexURLMapException('urlconf missing attribute %r' % attr_name)
        #log.debug(urls)
        self.callback_prefix = callback_prefix
        #self.label = app_label

        log.debug("Processing urlconf: %s"%type(urls))

        for instance in urls:
            if isinstance(instance, RegexURLPattern):
                pattern = prefix + instance.regex.pattern[0:]
                log.debug("Including pattern: %s" % pattern)
                try:
                    instance.__dict__['regex'] = re.compile(pattern, re.UNICODE)
                    if not instance.name:
                        instance.__dict__['name'] = app_label
                    #instance.__dict__['_callback_str'] = app_label
                    #instance.__dict__['_reverse_dict'] = instance.reverse_dict
                except re.error:
                    #   already included pattern, skip and continue parsing
                    #   the remaining patterns.
                    continue
                #self.add_routes(callback_prefix, *urls)
                self.makeroute(instance, app_label=instance.name)
            elif isinstance(instance, RegexURLResolver):
                self.makeroute(instance)
            else:
                #Not implemented
                #print type(instance)
                pass            
    
    def commit(self):
        """Freeze the routes. (cannot add anymore)"""
        self.routes = frozenset([item for item in self.routes])
        #self._commit_flag = True
        if self.debug:
            #print self.routes
            log.debug("Configured routes: %d" % len(self.routes))


    def __iter__(self):
        return iter(self.routes)

    def __next__(self):
        for item in self.routes:
            yield (item)

# default patterns for backward compatibility
# patterns = RegexURLMap()
