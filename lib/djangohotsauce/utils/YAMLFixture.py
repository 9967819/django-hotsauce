#!/usr/bin/env python
"""Generic fixture loading support independent from database driver.

To add support for a database backend, one must create a subclass
of the YAMLFixture class and override the ``create`` method. The
database driver must support fixtures to use the functions covered
in the YAMLFixture class.

Usage:

 >>> sampleData = YAMLFixture('/path/to/fixture.yaml')
 >>> sampleData.create(db) #NOTE: this is currently not implemented :)

"""
import os         # built-in
import posixpath  # built-in
import yaml       # requires pyyaml
import json # default/fallback json lib
json_encoder = json.encoder

__all__ = ['YAMLFixture']

class YAMLFixture(object):
    """A iterable YAML fixture loader class.

    Can be used to load multiple data structures contained
    in the same YAML file.

    >>> fixture = YAMLFixture('apps.yaml')
    >>> app_conf = fixture.get(app_label='restapp', category='web')
    >>> for obj in fixture.dumps():
    >>>    print obj
    >>> fixture.tojson() # etc...
    """

    #db = None

    def __init__(self, path, **kwargs):
        self.initial_kwargs = kwargs
        self.path = os.path.abspath(path)
        
        if 'schema_index_root' in kwargs:
            self.root = kwargs['schema_index_root']

        self.initial_data = self.safe_load(path)

    def get_index_root(self):
        """return the current index root -> str """
        if 'root' in self.__dict__.keys():
            return str(self.root)
        return None
        #raise ValueError('schema_index_root not set!')
    index_root = property(get_index_root)

    def create(self, db, **kwargs):
        """
        Override this method to customize how yaml data should
        be saved in the db.
        """
        raise NotImplementedError

    def safe_load(self, pathname):
        """Safe load a YAML file using the yaml.load method."""
            
        try:
            initial_data = yaml.load(open(pathname, 'r'))
        except (IOError, OSError):
            raise
        else:
            return initial_data

    load = staticmethod(safe_load)

    def __str__(self):
        return "<YAMLFixture path=%s>"%self.path

    cache = {}

    def __iter__(self):

        index_root = self.index_root
        # Attempt to create an iterator using data in self.initial_data, or
        # use the whole data set in case index_root is not usable.
        if index_root is not None and index_root in self.initial_data:
            iterable = iter(self.initial_data[self.index_root])
        else:
            # warning, deprecated stuff
            #print 'no usable index_root found, defaulting to slurp mode'
            iterable = iter(self.initial_data)

        return iterable

    def get(self, **kwargs):
        """
        Converts a list of params to a dict instance if matching
        the fixture item.

        """

        if not 'name' in kwargs:
            obj_id = str(hash(self))
        else:
            obj_id = kwargs['name']

        try:
            obj = self.cache[obj_id]
            #print "found obj in cache: %r" % obj_id
        except KeyError:
            obj = self.getdata(obj_id, **kwargs)
        
        if obj is not None:
            return obj
        else:    
            raise ValueError("no match found for %r" % str(self))
    
    def filter(self, **kwargs):
        """Return a sequence (list) of matching fixture items.
        
        """
        result = []
        for obj in self: # I'm a iterator
            for k, v in kwargs.iteritems():
                if obj[k].__contains__(v) or obj[k] == v:
                    result.append(obj)
                continue
        return result

    def getdata(self, obj_id, **kwargs):
        """
        Gets the cached object instance if available (dict), 
        otherwise do nothing.
        """
        for kw in self: # I'm a iterator
            #assert isinstance(kw, dict), 'kw must be a dict here'
            for k, v in kwargs.iteritems():
                if kw[k].__contains__(v) or kw[k] == v: 
                    # return the whole dictionary if the key
                    # is matching the corresponding value
                    self.cache[obj_id] = kw
                    return kw
                else:
                    continue    
        return
    
    def dumps(self):
        """Returns a list."""
        return [item for item in self]

    @property
    def all(self):
        return self.dumps()

    def tojson(self, filter_by={}, strict=False, escape_unicode=True):
        """Converts the list to json.
        
        ``filter_by``: If given, use that to selectively filter items in the
                       fixture
        """
        data = []
        if len(filter_by.keys()) >= 1:
            related_items = self.filter(**filter_by)
            data.extend(related_items)
        else:
            data.extend(self.dumps()) # default mode is a simple "dump all"
        
        return self.json_encode(data, strict=strict, escape_unicode=escape_unicode)

    def json_encode(self, value, **kwargs):
        """Encodes ``value`` in JSON format"""
        return json_encoder(value, **kwargs)
