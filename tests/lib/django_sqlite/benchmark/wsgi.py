"""
WSGI config for django111_pypy59 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
#import django

from django.core.wsgi import get_wsgi_application
#from django.core.handlers.wsgi import WSGIHandler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "benchmark.settings")
#django.setup()

#def application(environ, start_response):
#    return WSGIHandler()(environ, start_response)
application = get_wsgi_application()

