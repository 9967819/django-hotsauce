"""
This module provides a simple mecanism for getting a per-thread 
contextual session object.

For basic usage, simply import the ``ScopedSession`` object and
call ``set_session`` on a bound instance. 

The ``set_session`` argument requires a ``engine`` object as its first argument. 
Once this step is done the scoped session object should be bound to your engine 
and ready to use. 
"""
 
from sqlalchemy.orm import scoped_session, sessionmaker

__all__ = ['ScopedSession']

class ScopedSession(object):
    """  Contextual session wrapper """

    initialized = False
 
    def __init__(self, engine=None, **kwargs):
        
        self._session = None
        
        if engine is not None:
            self._engine = engine
            self.set_session(engine, **kwargs)
            self.initialized = True

    def get_session(self):
        """ Returns a Session instance object. """
        return getattr(self, '_session')

    def set_session(self, engine, autoflush=True, autocommit=False):
        """ Set up a default Session instance object. """
        local_session = scoped_session(sessionmaker(autoflush=autoflush, \
            autocommit=autocommit))
        # configure the Session object
        local_session.configure(bind=engine)
        self._session = local_session
        #self.initialized = True
        del local_session
        

    session = property(get_session, set_session)

