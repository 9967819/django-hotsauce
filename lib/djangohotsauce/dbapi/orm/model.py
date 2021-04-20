#!/usr/bin/env python
"""Base model classes for django-hotsauce"""
import logging
log = logging.getLogger(__name__)

from djangohotsauce.dbapi.orm import RelationProxy

__all__ = ['ModelManager']

class ModelManager(object):

    model = None # Category

    def __init__(self, connection=None, model=None, **kwargs):
        self.db = connection
        self.kwargs = kwargs
        if model is not None:
            self.model = model
        if connection is not None:
            self.objects = RelationProxy(getattr(connection, self.model))
        else:
            self.objects = None

    def __str__(self):
        return "<ModelManager: %s>" % self.model
   
    def find_or_create(self, **kwargs):
        try:
            obj = getattr(self.db, self.model).findone(**kwargs)
            if obj is not None:
                log.debug("Found object: %s!!!" % obj)
        except:
            # create
            tx = self.objects.t.create(**kwargs)
            self.db.execute(tx)
            self.db.commit()
            log.debug("Created new object: %s" % tx)
            obj = self.objects.get(**kwargs)
        return obj

    def save(self, commit=True):
        lock = self.db.write_lock()
        with lock:
            #if self.initialized:
            tx = self.extent.t.create(**self.kwargs)
            if commit:
                self.db.execute(tx)
                self.db._commit()
        lock.release()
        return self

