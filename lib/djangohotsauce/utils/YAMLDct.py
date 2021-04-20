#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""This module provide a convenient access to YAML files using the ``pyyaml``
extension as a Python dictionary.

Usage:
Require the presence of a ``CUSTOM_DATADIR`` setting to the value
of the directory holding the YAML files.`"""

import os, yaml, random
import posixpath

try:
    from io import open
except ImportError:
    pass

__all__ = ['YAMLDct', 'YAMLDctError', 'SortedYAMLDct', 'RandomYAMLDct']

class YAMLDctError(Exception):
    pass

class YAMLDct(object):
    """Returns a dict instance populated with the values 
    found in the YAML file"""

    def __init__(self, *args, **kwargs):
        pass

    def __new__(cls, path):
        return cls.openyamlfile(path)

    @classmethod
    def openyamlfile(cls, path):
        try:
            p = posixpath.realpath(path)
            with open(p, 'r') as f:
                aLst = yaml.load(f)
            f.close()    
        except (IOError, OSError) as error:
            raise YAMLDctError(error)
        return aLst

class SortedYAMLDct(YAMLDct):
    
    @classmethod
    def openyamlfile(cls, path):
        p = super(SortedYAMLDct, cls).openyamlfile(path)
        return sorted((item for item in p.iteritems()))

class RandomYAMLDct(YAMLDct):
    bits = 1
    
    @classmethod
    def openyamlfile(cls, path):
        p = super(RandomYAMLDct, cls).openyamlfile(path)
        random.seed(cls.bits)
        random.shuffle(p)
        return p

