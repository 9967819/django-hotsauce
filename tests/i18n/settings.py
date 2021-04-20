# Suck in default django settings
from django.conf.global_settings import *
from pkg_resources import resource_filename

DEBUG = True
USE_I18N = True

DEFAULT_CHARSET = 'UTF-8'
DEFAULT_CONTENT_TYPE = 'text/html; charset=%s' % DEFAULT_CHARSET

# Set this for debugging the template loader 
TEMPLATE_LOADERS_DEBUG = True

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    #'django.core.context_processors.debug'
)

# For backward-compatibility with Django
TEMPLATE_DIRS = (
    resource_filename('sandbox', 'templates'),
)

DATABASE_ENGINE = ''
DATABASE_NAME = 'sqlite:///fixtures/test.db'
#DATABASE_OPTIONS = {}
#DATABASE_ECHO = False

ROOT_URLCONF = 'urls'

