#!/usr/bin/env python
"""
Elixir Controller API (Elixir WSGI App)

Helper class to implement a generic WSGI handler supporting the
SQLElixir ORM on top of SQLAlchemy.

This module uses the ``ScopedSession`` class to provide persistent
connections to SQL databases using the ``threadlocal`` method.
"""

from importlib import import_module

# sqlalchemy required for Elixir to work! :-)
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

from wsgi import WSGIController

elixir_module = import_module('elixir')

__all__ = ['ElixirController']

class ElixirController(WSGIController):
    """
    A ``BaseController`` subclass supporting contextual sessions
    on top of Elixir/SQLAlchemy.
    """

    def __init__(self, engine_name, db_options={
        'echo': True,
        'strategy': 'threadlocal'
        }, **kwargs):
        """Setup the default Elixir parameters here"""

        self.db_options = db_options

        super(ElixirController, self).__init__(**kwargs)

        # if self.debug: assert 'settings' in self

        # Configure the Engine instance unless already defined
        self.set_engine(engine_name)
        # Prepare the database session to handle requests
        self.init_session(self.engine)
        # Set up the metadata obj
        self.metadata = MetaData(self.engine)

    def get_engine(self):
        """Returns a fully configured SQLAlchemy engine instance"""
        return getattr(self, '_engine')

    def set_engine(self, engine_name):
        """Setup a initial engine instance"""
        engine = create_engine(engine_name, **self.db_options)
        setattr(self, '_engine', engine)

        return None

    engine = property(get_engine, set_engine)

    def init_session(self, engine, shortnames=True, autoflush=True,
        autocommit=False):
        """
        Prepare the session backend and initialize ORM mapping
        for Elixir."""
        Session = scoped_session(sessionmaker(autoflush=autoflush))
        #Session.set_session(engine, autoflush=autoflush, autocommit=autocommit)

        ## replace the elixir session with our own
        ## http://cleverdevil.org/computing/68/
        elixir_module.session = Session
        elixir_module.options_defaults.update(dict(shortnames=bool(shortnames)))

        # setup_all
        if not elixir_module.metadata.is_bound():
            elixir_module.metadata.bind = engine

        # create tables if they're missing...
        # meta.create_all()

        # copy elixir.session to self.session
        # setattr(self, '_session', elixir.session)

    def __call__(self, environ, start_response):
        return self.application(environ, start_response)
