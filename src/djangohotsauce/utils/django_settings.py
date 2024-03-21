#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common utilities for working with Django settings modules."""

from djangohotsauce.storage.base import DataStore

__all__ = ['SettingsProxy', 'LazySettings']


class SettingsProxy(object):
    """
    A settings delegator object which returns a thread-local instance
    used for holding Django settings.
    """

    _settings_cache = {}
    _settings_module_name = 'DJANGO_SETTINGS_MODULE'
    
    def __init__(self, modname='local_settings', autoload=True):
        """Initialize default options for the ``SettingsProxy`` instance.
        
        Optional attributes ::

        ``autoload`` -- Set this to ``False`` to disable settings autoloading. By
        default, allow settings to be autoloaded during the controller
        initialization time.
        """

        try:
            _settings = self._settings_cache[modname]
        except KeyError:
            _settings = DataStore(modname, autoload=autoload)
    	
        # Install the settings object in _settings_cache
        self._settings_cache[modname] = _settings

    def __str__(self):
        return "<SettingsProxy: %s>" % str(self.settings)

class LazySettings(SettingsProxy):
    """Generic setting container based on SettingsProxy"""

    def __init__(self, **kwargs):
        if not 'autoload' in kwargs:
            kwargs['autoload'] = True
        super(LazySettings, self).__init__(**kwargs)

    def __new__(cls, *args, **kwargs):
        pyobj = object.__new__(cls, *args, **kwargs)
        pyobj.__init__()

