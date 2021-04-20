#from sandbox_sqlalchemy.config.settings import *
#from sandbox.config.settings import *
from moviereviews.config.settings import *

DEBUG = True
ENABLE_BEAKER = True
SECRET_KEY = '12344dsdsd'
TEMPLATE_LOADER = 'notmm.utils.template.backends.CachedTemplateLoader'

PUBSUB_ERROR_HANDLERS = CUSTOM_ERROR_HANDLERS
