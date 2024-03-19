# Suck in default django settings
from django.conf.global_settings import *

from pkg_resources import resource_filename

import os

DEBUG = True
USE_I18N = True

# Custom error handlers mapping
CUSTOM_ERROR_HANDLERS = (
    #('handle401', 'sandbox.handlers.handle401'),
    #('handle403', 'sandbox.handlers.handle403'),
    ('handle404', 'sandbox.handlers.handle404'),
    ('handle500', 'sandbox.handlers.handle500')
    )

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
#TEMPLATE_CONTEXT_PROCESSORS = (
#    'django.contrib.auth.context_processors.auth',
#    'blogengine.contrib.i18n.context_processors.i18n'
#    )
TEMPLATE_CONTEXT_PROCESSORS = ()

# For backward-compatibility with Django
TEMPLATE_DIRS = (
    resource_filename('sandbox', 'templates'),
)

ROOT_URLCONF = 'sandbox.config.urls'

MIDDLEWARE_CLASSES = ()

#SITE_ID = 1

#a new method for changing django INSTALLED_APPS behavior 
#is described here:
#   [type] the model type (default: "native") (Django legacy orm)
#   [debug] turn debug on for this app..
#   [profile] turn profiling on for the app
#INSTALLED_APPS = (
#    'django.contrib.auth', 
#    'django.contrib.admin',
#    'django.contrib.sessions',
#    'django.contrib.contenttypes'
#    )
INSTALLED_APPS = ()

ENABLE_TIDYLIB = False

ENABLE_LOGGING = True
LOGGING_CALLBACK = 'rootLogger'
