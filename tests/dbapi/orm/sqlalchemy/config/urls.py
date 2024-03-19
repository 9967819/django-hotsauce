#!/usr/bin/env python
# -*- coding: utf-8 -*-

from notmm.utils.urlmap import RegexURLMap, url

urlpatterns = RegexURLMap()
urlpatterns.add_routes('',
        # Frontdoor (a simple generic view)
        (r'^index.html|$', 'sandbox.views.index', {
            'template_name': 'sandbox/test.mako',
            'charset': 'utf-8' # must specify mimetype or charset
        })
)
urlpatterns.include('sandbox.config.extras')
