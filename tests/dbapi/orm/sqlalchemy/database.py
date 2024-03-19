#!/usr/bin/env python

import sqlalchemy
import sandbox

from pkg_resources import resource_filename
from sqlalchemy.orm              import scoped_session, sessionmaker

from notmm.utils.django_settings import LazySettings

# init the local application data store
app_conf = sandbox.global_conf['sandbox']

# init the settings module (thread-local)
settings = LazySettings()

# SQLAlchemy settings
backend = app_conf['backend']
schema = backend + ':///' + resource_filename('sandbox', app_conf['path'])

engine = sqlalchemy.create_engine(schema, echo=app_conf['echo'])
metadata = sqlalchemy.MetaData(engine)
Session = scoped_session(sessionmaker(bind=engine))

