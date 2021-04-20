"""Simplified ORM abstraction module for Schevo""" 

from ._databaseproxy import DatabaseProxy, ConnectionError
from ._relation import RelationProxy
#deprecated
#from .schevo_compat import XdserverProxy
from .zodb_compat import ClientStorageProxy

