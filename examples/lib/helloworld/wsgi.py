#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
from notmm.adapters.utils import make_app
from notmm.utils.django_settings import LazySettings

settings = LazySettings()
wsgi_app = make_app(settings, enable_oauth=False)

def application(environ, start_response):
    #if environ['django.settings'].OAUTH2_DISABLE:
    #    enable_oauth = False
    #else:
    #    enable_oauth = True
    return wsgi_app(environ, start_response)

