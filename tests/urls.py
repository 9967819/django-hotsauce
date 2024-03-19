#!/usr/bin/env python
# -*- coding: utf-8 -*-

from djangohotsauce.utils.urlmap import RegexURLMap, url
from djangohotsauce.utils.template import direct_to_template

# a custom/generic login view
handleLogin = 'blogengine.contrib.session.login'
handleLogout = 'blogengine.contrib.session.logout'

urlpatterns = RegexURLMap()
urlpatterns.add_routes('sandbox.views',
        url(r'^$|index.html$', 'index', {
            'template_name': 'sandbox/test.mako',
            'charset': 'utf-8' # must specify mimetype or charset
        }),
)
# Add the authentication views
urlpatterns.add_routes('',
        # Custom authentication backend wrapper (authkit based)
        # see nomainapp..controllers.auth.LoginController
        url(r'^session_login/$', handleLogin, \
            dict(template_name='auth/login.mako')),
        url(r'^session_logout/$', handleLogout, \
            dict(template_name='auth/logout.mako')),
)

#urlpatterns.include('sandbox.config.extras')

#blogengine api v1
#urlpatterns.include('blogengine.contrib.api_v1.urls', prefix="^blog/")


