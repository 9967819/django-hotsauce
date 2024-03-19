#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

#handle200 = 'notmm.lib.wsgiapp.render_to_response'

urlpatterns = patterns('',
        # Frontdoor (a simple generic view)
        (r'^$', 'sandbox.views.index', {
            'template_name' : 'sandbox/test.mako'
        }),
        (r'^croak$', 'sandbox.views.croak'),
        # with_session decorator test
        (r'^test$', 'sandbox.views.test_session', {
            'template_name' : 'sandbox/test.mako'
        }),
        # with_schevo_database test
        (r'^test.schevo$', 'sandbox.views.test_schevo_database', {
            'template_name' : 'sandbox/test.mako'
        }),
        (r'^moved/$', 'sandbox.handlers.handle302', {
            'location' : '/index.html'
        })
)

