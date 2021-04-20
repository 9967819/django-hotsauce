#!/usr/bin/env python
"""Customized wrappers over ``mako.lookup.TemplateLookup``.

Provides Mako templates loading and rendering extra customizations
to extend the ``TemplateLookup`` class.

"""

import mako.lookup as model


__all__ = ('UnicodeTemplateLoader', 'BaseTemplateLoader', 'CachedTemplateLoader')
class BaseTemplateLoader(model.TemplateLookup):
    """Minimal and fast template loader based on TemplateLookup."""
    collection_size = 48
    cache_enabled = False       # False=Disables template caching by default
    filesystem_checks = False   # False=Disables template reloading

class UnicodeTemplateLoader(BaseTemplateLoader):
    """Preconfigured template loader with generic Unicode bytestrings support"""
    cache_enabled = False
    default_filters = ['unicode'] # 'decode.utf8'
    input_encoding = 'UTF-8'
    encoding_errors = 'xmlcharrefreplace' # Rewrite Unicode encoding errors (when possible)
    #encoding_errors = 'replace'

class CachedTemplateLoader(UnicodeTemplateLoader):
    """Enables templates caching using selected cache backend (beaker)"""
    cache_enabled = True
    cache_impl='beaker'
