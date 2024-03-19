#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.shortcuts import render_to_response
from notmm.dbapi.orm import decorators, sql

from notmm.utils.configparse import loadconf

from sandbox                import configuration as c

app_conf = loadconf('development.ini', section='moviereviews')
verbose = (app_conf['verbose'] == "true")

# generic view with positional arguments and kwargs
def index(request, **kwargs):
    return render_to_response(request, **kwargs)

# faked 500 error handling
def croak(request, template_name='500.mako'):
    return render_to_response(request, template_name, status=500)

# experimental scoped_session support for Django views
@with_session(engine=c.engine)
def test_session(request, **kwds):

    template_name = kwds['template_name']
    # app._scoped_session
    assert request.environ['_scoped_session'] != None

    return render_to_response(request, template_name)

@with_schevo_database(app_conf)
def test_schevo_database(request, **kwds):
    print 'in test_schevo_database'
    db = request.environ['schevo.db.moviereviews']
    assert db.format == 2, 'invalid db format: %d' % db.format
    assert hasattr(db, 'Q'), 'db has no Q attribute!'
    Q = db.Q
    movies = (item for item in db.Movie.find())
    #if verbose:
    #    for x in movies:
    #        print x
    db.close()
    return render_to_response(request, **kwds)
    
