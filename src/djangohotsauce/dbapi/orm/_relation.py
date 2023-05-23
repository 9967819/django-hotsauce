#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Generic object-relational mapper (ORM) for manipulating Schevo/Durus 
databases.
"""
from operator import attrgetter

__all__ = ['RelationProxy']

class RelationProxy(object):
    """
    Allow access to a ``Extent`` object using a referenced
    string value.

        >>> objects = RelationProxy(db.User)
        >>> objects.all()
        >>> user = objects.get(username="corina")
        >>> assert str(objects) == '<RelationProxy: User>'
        >>> user2 = objects.get_by_oid(oid)
    """
    
    def __init__(self, reference):
        """Constructor method.
        params:
        ``reference``: A valid Extent class reference (str).
        """
        self.extent = reference
        self.t = getattr(reference, 't')
        self.name = str(self.extent.name)

    def all(self, **params):
        """Return all entities for a Extent."""
        if 'order_by' in params.keys():
            order_by = params.pop('order_by')
        else:
            order_by = None
        values = [item for item in self.extent.find(**params)]
        if (order_by and isinstance(order_by, str)):
            return self._order_by(values, order_by)
        else:    
            return values

    def get(self, **kwargs):
        """Get method to retrieve a single ``Entity`` object."""
        return self.extent.findone(**kwargs)
    
    def save(self, data):
        """
        Save a new record for a ``Extent`` instance (transaction wrapper)
        """
        return NotImplementedError

    def update(self, oid, data):
        """
        Update operation (Transaction wrapper)
        """
        return NotImplementedError
    
    def delete(self, oid):
        """
        Delete operation (Transaction wrapper)
        """
        return NotImplementedError
    
    def get_by_oid(self, oid):
        """
        Lookup a individual entity record using ``oid`` as the
        primary key, return None if no record was found.
        
        """
        #db = self.extent.db
        
        try:
            obj = self.extent[int(oid)]
        except KeyError:
            # no such object with such OID exists
            #raise ObjectDoesNotExist(e)
            raise
        return obj

    def _order_by(self, data, order_by):
        """Return a list of entities sorted by a field attribute."""
        values = sorted(data, key=attrgetter(order_by))
        values.reverse()
        return values
    order_by = _order_by

    def find(self, **kwargs):
        order_by = kwargs.pop('pub_date', None)
        objs = self.extent.find(**kwargs)
        if order_by:
            return self.order_by(objs, order_by)
        else:
            return objs

    def __str__(self):
        return "<RelationProxy: %s>" % self.name
    
