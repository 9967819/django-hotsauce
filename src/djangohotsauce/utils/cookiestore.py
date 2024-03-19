#!/usr/bin/env python
"""Cookie Storage API

A cookie store to use for storage of session data.
"""
__all__ = ['CookieStore']

class CookieStore(object):
    """A generic session storage abstract class

    """

    # Picker (Pickle) protocol emulation (unfinished/not tested)
    #def __getstate__(self):
    #    return
    #def __setstate__(self, state):
    #   return

    def __init__(self, key=None):
        #self._data = threading.local()
        self._data = {}
        self._sessionkey = key

    def get_storage(self):
        return self._data

    _session = property(get_storage)

    def __getattr__(self, value, default=None):
        return self._session.get(value, default)

    def __getitem__(self, value, default=None):
        return self.__getattr__(value, default)

    def __setitem__(self, key, value):
        self._session[key] = value

    def __delitem__(self, value):
        del self._session[value]

    def __contains__(self, value):
        return value in self._session

    # public methods
    def get(self, value, default=None):
        return self.__getitem__(value, default)

    #def get_and_delete_messages(self):
    #    pass

    # iteration procotol
    #def __next__(self):
    #    for item in iter(self):
    #        yield item
    #def __iter__(self):
    #    return self.__dict__.iteritems()
