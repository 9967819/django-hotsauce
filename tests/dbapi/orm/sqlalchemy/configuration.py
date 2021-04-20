import sandbox

from pkg_resources import resource_filename

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

from notmm.utils.django_settings import LazySettings
from notmm.utils.configparse import as_bool

# init the local application data store
app_conf = sandbox.global_conf['sandbox']

# init the settings module (thread-local)
settings = LazySettings()

# SQLAlchemy settings
backend = app_conf['backend']
schema = backend + ':///' + resource_filename('sandbox', app_conf['path'])

engine = create_engine(schema, echo=as_bool(app_conf['echo']))
metadata = MetaData(engine)
Session = scoped_session(sessionmaker(bind=engine))

