#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.
#
# This file is part of the djangohotsauce distribution.
# Please review the LICENSE file for details.

"""DataStore API

The DataStore API provides a simplified environment for storing
user/system data. It should be noted that the current state of 
the API is still in an early alpha stage and is subject to change.
"""

__all__ = ['BaseStore', 'DataStore']

import posixpath
import copy
from djangohotsauce.utils.configparse import is_uppercase


class BaseStore(object):
    """Base class for storing and loading objects."""

    def __init__(self):
        pass

    def count(self):
        """
        count the number of objects in UPPER_CASE found
        in __dict__ and return that number. Note that
        only UPPER_CASE keys are being counted.
        """
        return len([ key for key in self.__dict__ if is_uppercase(key) ])  

    def clear(self):
        """ remove everything that looks like a setting option """
        for key, val in self.__dict__.items():
            if is_uppercase(key):
                del self.__dict__[key]
        # reset the initialized object..
        #self.initialized = False
        # and always return something..
        return self


class DataStore(BaseStore):
    """Wrapper to store local data in a single thread"""
   
    _initialized = False
    _default_modname = 'local_settings'
    
    def __init__(self, modname, autoload=True):
        """Implements the __init__ method for ThreadLocalStore instances.
        
        Automatically load the objects contained in ``modname`` if autoload is True.
        """

        # This init code was borrowed from the 
        # _threading_local module.
        self._modname = modname
        self._local_data = {}
        
        if autoload and not self._initialized:
            self.loads(modname)

    def loads(self, modname=None):
        """ 
        Load objects from `modname` using the `__import__`
        builtin function.
        """
        if not modname:
            #raise ValueError("Missing modname parameter.")
            modname = self.default_modname

        head, tail = posixpath.splitext(modname)
        module_name = tail.lstrip('.')
        # this must handle both absolute and relative imports
        m_obj = __import__(modname, {}, {}, fromlist=[module_name])
        # Copy the precious settings into our thread-safe 
        # storing class.
        if m_obj:
            for key in m_obj.__dict__:
                self._local_data[key] = m_obj.__dict__[key]
            self.__dict__ = self._local_data.copy()
            self.__dict__['_modname'] = modname
            self.__dict__['_initialized'] = True
        return self

    def __iter__(self):
        return iter(self.__dict__)

    def __next__(self):
        for item in self.__dict__.iteritems():
            yield item
    
    def __getitem__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            raise

    def __setitem__(self, name, value):
        try:
            self.__dict__[name] = value
        except Exception:
            raise

    def __str__(self):
        return "%s" % self._modname

ThreadLocalStore = DataStore # for backward-compatibility

