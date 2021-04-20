#!/usr/bin/env python

import re, logging
from importlib import import_module
from django.core.exceptions import ImproperlyConfigured, ViewDoesNotExist
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import iri_to_uri, force_text, smart_str
from django.utils.regex_helper import normalize
from functools import wraps

try:
    from django.utils.lru_cache import lru_cache
    def memoize(func, cache, num_args):
        return lru_cache()(func)
except ImportError:
    from django.utils.functional import memoize

log = logging.getLogger(__name__)

try:
    reversed
except NameError:
    from django.utils.itercompat import reversed     # Python 2.3 fallback
    from sets import Set as set

_resolver_cache = {} # Maps URLconf modules to RegexURLResolver instances.
_callable_cache = {} # Maps view and url pattern names to their view functions.

class NoReverseMatch(BaseException):
    # Don't make this raise an error when used in a template.
    silent_variable_failure = True

def get_callable(lookup_view, can_fail=True):
    """
    Convert a string version of a function name to the callable object.

    If the lookup_view is not an import path, it is assumed to be a URL pattern
    label and the original string is returned.

    If can_fail is True, lookup_view might be a URL pattern label, so errors
    during the import fail and the string is returned.

    """
    if not callable(lookup_view):
        try:
            mod_name, func_name = get_mod_func(str(lookup_view))
            lookup_view = getattr(import_module(mod_name), func_name)
        except (ImportError, AttributeError):
            if can_fail: raise
        except UnicodeEncodeError:
            pass
    return lookup_view

get_callable = memoize(get_callable, _callable_cache, 1)

def get_resolver(urlconf, settings=None):
    if urlconf is None:
        if settings is None:
            from djangohotsauce.utils.django_settings import LazySettings
            settings = LazySettings()
            urlconf = settings.ROOT_URLCONF
    return RegexURLResolver(r'^/', urlconf)
get_resolver = memoize(get_resolver, _resolver_cache, 1)

def get_mod_func(callback):
    # Converts 'django.views.news.stories.story_detail' to
    # ['django.views.news.stories', 'story_detail']
    try:
        dot = callback.rindex('.')
    except ValueError:
        return callback, ''
    return callback[:dot], callback[dot+1:]

class RegexURLPattern(object):
    def __init__(self, regex, callback, default_args=None, name=''):
        # regex is a string representing a regular expression.
        # callback is either a string like 'foo.views.news.stories.story_detail'
        # which represents the path to a module and a view function name, or a
        # callable object (view).
        self.regex = re.compile(regex, re.UNICODE)
        
        if callable(callback):
            self._callback = callback
        else:
            self._callback = None
            self._callback_str = callback

        self.default_args = default_args or {}
        self.name = name
    
    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__, self.name, self.regex.pattern)

    def add_prefix(self, prefix):
        """
        Adds the prefix string to a string-based callback.
        """
        if not prefix or not hasattr(self, '_callback_str'):
            return
        self._callback_str = prefix + '.' + self._callback_str

    def resolve(self, path):
        match = self.regex.search(force_text(path))
        if match:
            # If there are any named groups, use those as kwargs, ignoring
            # non-named groups. Otherwise, pass all non-named arguments as
            # positional arguments.
            kwargs = match.groupdict()
            if kwargs:
                args = ()
            else:
                args = match.groups()
            # In both cases, pass any extra_kwargs as **kwargs.
            kwargs.update(self.default_args)

            return (self.callback, args, kwargs)

    def _get_callback(self):
        
        if self._callback is not None:
            return self._callback
        else:
            try:
                mod_name, func_name = get_mod_func(str(self._callback_str))
                self._callback = getattr(import_module(mod_name), func_name)
            except Exception as e:
                exc_type = type(e)
                raise 
            else:
                return self._callback
    callback = property(_get_callback)

class RegexURLResolver(object):
    def __init__(self, regex, urlconf_name, default_kwargs=None, app_name=None, namespace=None, debug=False):
        # regex is a string representing a regular expression.
        # urlconf_name is a string representing the module containing URLconfs.
        self.regex = re.compile(regex, re.UNICODE)
        self.urlconf_name = urlconf_name
        if not isinstance(urlconf_name, str):
            self._urlconf_module = self.urlconf_name
        self.callback = None
        self.default_kwargs = default_kwargs or {}
        self.app_name = app_name
        self.namespace = namespace
        self._reverse_dict = {}
        self.debug = debug

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__, self.urlconf_name, self.regex.pattern)

    def _get_reverse_dict(self):
        # a test case would be great 
        if hasattr(self, '_reverse_dict'):
            lookups = MultiValueDict(self._reverse_dict)
            for pattern in reversed([item for item in self.url_patterns]):
                if pattern is not None:
                    p_pattern = pattern.regex.pattern
                    if p_pattern.startswith('^'):
                        p_pattern = p_pattern[1:]
                else:
                    p_pattern = None
                if isinstance(pattern, RegexURLResolver):
                    parent = normalize(pattern.regex.pattern)
                    for name in pattern.reverse_dict:
                        for matches, pat in pattern.reverse_dict.getlist(name):
                            new_matches = []
                            for piece, p_args in parent:
                                new_matches.extend([(piece + suffix, p_args + args) for (suffix, args) in matches])
                            lookups.appendlist(name, (new_matches, p_pattern + pat))
                else:
                    if p_pattern:
                        bits = normalize(p_pattern)
                        #lookups.appendlist(pattern.callback, (bits, p_pattern))
                        if hasattr(pattern, 'name'):
                            lookups.appendlist(pattern.name, (bits, p_pattern))

            self._reverse_dict = lookups
        return self._reverse_dict
    reverse_dict = property(_get_reverse_dict)

    def resolve(self, path):
        match = self.regex.search(force_text(path))
        if match:
            #if self.debug: 
            #    log.debug("Got a match: %s"%path)
            new_path = path[match.end():]
            for pattern in self.url_patterns:
                try:
                    if pattern is not None:
                        
                        sub_match = pattern.resolve(new_path)
                except NoReverseMatch:
                    #log.debug(e)
                    #log.debug("caught a unknown path: %s"%new_path)
                    sub_match = None
                else:
                    if sub_match:
                        #if self.debug:
                        #    log.debug("Got sub_match: %r"%repr(sub_match))
                        sub_match_dict = dict([(k, v) for k, v in match.groupdict().items()])
                        sub_match_dict.update(self.default_kwargs)
                        for k, v in sub_match[2].items():
                            sub_match_dict[k] = v
                        return (sub_match[0], sub_match[1], sub_match_dict)
            raise NoReverseMatch('Resource not found: %s'%new_path)
        return None

    def _get_urlconf_module(self):
        try:
            return self._urlconf_module
        except AttributeError:
            self._urlconf_module = import_module(self.urlconf_name)
            return self._urlconf_module
    urlconf_module = property(_get_urlconf_module)

    def _get_url_patterns(self):
        patterns = getattr(self.urlconf_module, "urlpatterns", self.urlconf_module)
        try:
            iter(patterns)
        except TypeError:
            raise ImproperlyConfigured("The included urlconf %s doesn't have any "
                "patterns in it" % self.urlconf_name)
        return patterns
    url_patterns = property(_get_url_patterns)

    def _resolve_special(self, view_type):
        callback = getattr(self.urlconf_module, 'handler%s' % view_type, None)
        #if not callback: 
 		#    # Lazy import, since urls.defaults imports this file
        #    # See http://code.djangoproject.com/attachment/ticket/5350/urlresolvers.patch
 		#    from django.conf.urls import defaults 
 		#    callback=getattr(defaults, 'handler%s' % view_type) 
        
        mod_name, func_name = get_mod_func(callback)
        try:
            return getattr(import_module(mod_name), func_name), {}
        except (ImportError, AttributeError) as e:
            raise ViewDoesNotExist("Tried %s. Error was: %s" % (callback, str(e)))

    def resolve404(self):
        return self._resolve_special('404')

    def resolve500(self):
        return self._resolve_special('500')

    def reverse(self, lookup_view, *args, **kwargs):
        #try:
        #    lookup_view = get_callable(lookup_view, True)
        #except (ImportError, AttributeError), e:
        #    raise NoReverseMatch("Error importing '%s': %s." % (lookup_view, e))       
        possibilities = self.reverse_dict.getlist(lookup_view)
        for possibility, pattern in possibilities:
            # result is callable
            for result, params in possibility:
                if args:
                    if len(args) != len(params):
                        continue
                    unicode_args = [force_text(val) for val in args]
                    candidate =  result % dict(zip(params, unicode_args))
                else:
                    if set(kwargs.keys()) != set(params):
                        continue
                    unicode_kwargs = dict([(k, force_text(v)) for (k, v) in kwargs.items()])
                    candidate = result % unicode_kwargs
                if re.search(u'^%s' % pattern, candidate, re.UNICODE):
                    return candidate
        raise NoReverseMatch("Reverse for '%s' with arguments '%s' and keyword "
                "arguments '%s' not found." % (lookup_view, args, kwargs))

def resolve(path, urlconf=None):
    return get_resolver(urlconf).resolve(path)

def reverse(viewname, request, urlconf=None, args=[], kwargs={}, prefix='/'):
    #XXX fix me
    resolver = get_resolver(urlconf)
    return iri_to_uri("%s%s" % (prefix, resolver.reverse(
            viewname, *args, **kwargs)
            ))

def is_valid_path(path, urlconf=None):
    """
    Returns True if the given path resolves against the default URL resolver,
    False otherwise.

    This is a convenience method to make working with "is this a match?" cases
    easier, avoiding unnecessarily indented try...except blocks.
    """
    try:
        resolve(path, urlconf)
        return True
    except NoReverseMatch:
        return False
