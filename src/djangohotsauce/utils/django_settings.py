#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common utilities for working with Django settings modules."""

import os, sys, threading

from functools import wraps
from djangohotsauce.datastore import DataStore
from djangohotsauce.utils.django_compat import memoize


__all__ = ['SettingsProxy', 'LazySettings']


class SettingsProxy(object):
    """
    A settings delegator object which returns a thread-local instance
    used for holding Django settings.
    """

    _settings_cache = {}
    _settings_module_name = 'DJANGO_SETTINGS_MODULE'
    
    def __init__(self, modname=None, autoload=True):
        """Initialize default options for the SettingsProxy instance
        
        Optional attributes:

        ``autoload`` -- Set to ``False`` to disable settings autoloading. By
        default, allow settings to be autoloaded during the controller
        initialization time.
        """

        # ensure to initialize _settings_cache
        self._settings_cache.clear()
        self.initsettings(name=modname)
        #if modname in sys.modules:
        #    #print 'doing a coup..'
        #    self._settings_cache[modname] = sys.modules[modname]

        # set autoload flag for django settings
        self.autoload = autoload
               
    def get_settings(self):
        """ Returns a ready-to-use LocalStore instance. """
        try:
            _settings = self._settings_cache[self.modname]
        except KeyError:
            #print "module %s not found in cache!" % self.modname
            # Use the provided settings module name
            _settings = DataStore(self.modname, autoload=self.autoload)
    	# Install the settings object in _settings_cache
        else:
            if not self.modname in self._settings_cache:
                self._settings_cache[self.modname] = _settings
        return _settings   


    def __str__(self):
        return "<SettingsProxy: %s>" % str(self.settings)

    def __call__(self):
        
        lock = threading.Lock()

        with lock:
            lock.acquire()
            try:
                return self.get_settings()
            finally:
                lock.release()

    def destroysettings(self, name):
        self._settings_cache.clear()
        return None
    
    def initsettings(self, name=None):
        self.destroysettings(name)
        if name is None:
            self.modname = os.environ[getattr(self, '_settings_module_name')]
        else:
            self.modname = name


    settings = property(memoize(get_settings, _settings_cache, 1))
    

class LazySettings(SettingsProxy):
    """Generic setting container based on SettingsProxy"""

    def __init__(self, **kwargs):
        if not 'autoload' in kwargs:
            kwargs['autoload'] = True
        super(LazySettings, self).__init__(**kwargs)

    def __new__(cls, *args, **kwargs):
        pyobj = object.__new__(cls, *args, **kwargs)
        pyobj.__init__()
        return pyobj.get_settings()

