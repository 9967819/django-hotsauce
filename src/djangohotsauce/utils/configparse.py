#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007-2013 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.
#
# <LICENSE=APACHEV2>
#
"""Misc utilities for parsing configuration files in RFC-822 format."""

import os
import sys
import posixpath
from configobj import ConfigObj

__all__ = ('string_getter', 'int_getter', 'long_getter', 
           'is_string', 'is_utf8', 'make_path',
           'has_conf', 'is_equal', 'is_uppercase', 
           'loadconf', 'getconf', 'make_path', 'setup_all',
           'as_bool', 'paste_eval_import', 'eval_import')

# conf_getters like functions
string_getter = lambda conf,section,key: str(conf[section].get(key, None))

# builtin numeric-like getters: wtf?
# i don't remember using thoses for a while.. :)
int_getter = lambda *s: int(string_getter(*s))
long_getter = lambda *s: long(int_getter(*s))

### more string-like hooks; 
#this one returns a boolean
is_string = lambda s: bool(isinstance(s, str))
# verifies if the string is encoded in utf8 format
is_utf8 = lambda s: bool(isinstance(s, unicode))
### "path" functions
make_path = lambda relname: posixpath.realpath(posixpath.abspath(relname))
has_conf = lambda x, y: os.access (posixpath.join (x, y), os.R_OK)
### logic related test functions
is_equal = lambda a, b: bool(a==b)
is_uppercase = lambda s: bool(s.isupper())

# Emulate ``paste.util.converters.asbool`` but using 
# ``configobj.as_bool`` semantics.
as_bool = lambda cfg, v: cfg.as_bool(v)

def loadconf(filename, section=None, config_class=ConfigObj):
    """ 
    Returns a fully configured ConfigObj instance.

    """
    app_conf = config_class(make_path(filename))
    if section in app_conf:
        return app_conf[section]
    else:
        return app_conf   

def getconf(relname):
    """Loads a configuration file and return its content."""
    # Default options are now located in development.ini.
    return loadconf(relname)

def setup_all(key, global_conf, c='development.ini'):
    """
    Loads development (config) options required for running an
    application and put them in the application global 
    configuration dict, as referenced by ``key``, or else 
    into a similar persistent storage object.

    Returns ``False`` on success, or ``True`` if no development.ini
    file has been found.

    This function is optional, and should not be necessary 
    for normal operations. 
    """
    
    if has_conf(os.getcwd(), c):
        # Add a reference to ``key`` in the dict instance ``global_conf`` 
        global_conf.update({key: loadconf(c, section=key).dict()})
        return False
    return True


def paste_eval_import(name):
    """Helper function to avoid installing Paste as requirement"""
    from pastelib import eval_import
    return eval_import(name)

eval_import = lambda s: paste_eval_import(s)
