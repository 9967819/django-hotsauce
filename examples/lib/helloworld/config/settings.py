#Global settings for the helloworld app, to be overrided in local_settings.py.
from django.conf.global_settings import *
from pkg_resources import resource_filename
MEDIA_ROOT = resource_filename('helloworld', 'static')
ROOT_URLCONF='helloworld.config.urls'
#ENABLE_BEAKER=False
MEDIA_URL="http://localhost/media/img/"
SECRET_KEY='12345va1110ht'
#ENABLE_TIDYLIB=False
DEBUG=True

#I18N stuff (experimental)
USE_I18N=False
LANGUAGE_CODE = 'fr-CA'
DEFAULT_CHARSET = 'utf-8'
DEFAULT_CONTENT_TYPE = 'text/html; charset=%s' % DEFAULT_CHARSET

# Custom error handlers mapping
CUSTOM_ERROR_HANDLERS = (
    ('handle302', 'helloworld.handlers.handle302'),
    ('handle404', 'helloworld.handlers.handle404'),
    ('handle500', 'helloworld.handlers.handle500'),
)

# For backward-compatibility with Django.
# Import templates from the package name.
TEMPLATE_DIRS = (
    (resource_filename('helloworld', 'templates')),
)
TEMPLATE_LOADER = 'notmm.utils.template.backends.CachedTemplateLoader'

# Logging options
LOGGING_FORMAT = '[%(levelname)-5s] - [%(asctime)-15s] - [%(name)-5s] - %(message)s' 
# Where to send application errors 
LOGGING_ERROR_LOG = '/var/log/django.log'

TEMPLATE_CONTEXT_PROCESSORS = (
    'helloworld.config.context_processors.request',
    )
OAUTH2_CLIENT_ID = '51290408562-abs4t4ecqo834diltkk3d42cef6fi2sd.apps.googleusercontent.com'
OAUTH2_ACCESS_TOKEN = 'd5RM8aoiHBET3Fu5kUBqwDGg'
OAUTH2_REDIRECT_URL = 'http://localhost:8000/oauth2callback'

