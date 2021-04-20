#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2008 Jack Bortone <jack@isotopesoftware.ca>

"""Utilities for manipulation of metadata objects"""

__all__ = ['get_mapper']

def get_mapper(entity, meta, engine, autoload=True):
    """
    Setup and return a `sqlalchemy.orm.mapper` object for
    a given entity.
    """
    from sqlalchemy.orm import class_mapper
    if not meta.is_bound():
        # bind to `engine' if not already done
        meta.bind = engine
    mapper = class_mapper(entity)
    return mapper

