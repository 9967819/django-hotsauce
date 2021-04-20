#!/usr/bin/env python
#
"""Configuration options for template rendering and
parsing.

This class provides a compatibility bridge between customizable 
template backends and the Django ``RequestContext`` object.

TODO: Add support for Genshi templates.
"""
import os
from mako.exceptions import MakoException

from djangohotsauce.utils.template.interfaces import TemplateLoaderFactory
from djangohotsauce.utils.django_settings import SettingsProxy

__all__ = ('get_template_loader', 'MakoTemplateException', 'TemplateException')


class MakoTemplateException(MakoException):
    pass

class TemplateException(MakoTemplateException):
    pass

# register a default template backend instance 
def get_template_loader(
    backend="djangohotsauce.utils.template.backends.UnicodeTemplateLoader",
    cache_enable=False
    ):

    _settings = SettingsProxy(autoload=True).get_settings()
    #_cache_enabled = getattr(_settings, 'ENABLE_BEAKER', cache_enabled)
    
    directories = _settings.TEMPLATE_DIRS

    TemplateLoaderFactory.configure(backend, directories=directories)
    loader = TemplateLoaderFactory.get_loader()
    return loader

