#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007-2013 Jack Bortone <jack@isotopesoftware.ca>
# All rights reserved.
#
# <LICENSE=ISC> 
"""
Security views for authentication and authorization of registered users based on their
role and permissions. Custom permissions and roles may be configured using the
Authkit library.
"""

import time
import hashlib
import logging
import forms

#from pubsub import pub
#import beaker.session
from notmm.utils.configparse import loadconf
from notmm.utils.wsgilib     import HTTPRedirectResponse
from notmm.controllers.auth  import AuthCookieController

from notmm.utils.template    import direct_to_template
from authkit.authenticate   import valid_password
from authkit.permissions    import RemoteUser
from authkit.authorize      import NotAuthenticatedError

from test_support import (
    WSGIControllerTestCase, 
    TestClient, 
    unittest,
    make_app,
    settings
    )

log = logging.getLogger('notmm.controllers.wsgi')
auth_conf = loadconf('development.ini', section='authkit')


class LoginControllerTestCase(WSGIControllerTestCase):
    
    def test_authenticate_user(self): 
        def authenticate_user(request, username, password, tokens='', 
            user_data=time.ctime,
            authfunc='authkit.set_user'):
            #"""Authenticate the user into the site and update the last_modified
            #timestamp if authentication and authorization granted user access."""

            # Add the cookie middleware
            # secret = hashlib.md5(username).hexdigest()
            # request = AuthTKTMiddleware(request, secret)
            request = AuthCookieController(request, auth_conf=auth_conf, settings=None)
            try:
                user_setter_func = request.environ[authfunc]
                if valid_password(request.environ, username, password):
                    user_setter_func(username, tokens=tokens, user_data=user_data())
                    #trigger function here to update the last_modified timestamp 
                    log.debug('User %s has been authenticated and authorized access!!' % username)
                raise NotAuthenticatedError
            except (KeyError, Exception):
                raise NotAuthenticatedError
            return None
    
def logout(request, template_name='auth/logout.html',
    logout_func='authkit.logout_user', user_func='authkit.set_user', 
    session_key='beaker.session', urlto='/'):
    for key in ('REMOTE_USER', 'USER'):
        if key in request.environ.keys():
            del request.environ[key]
            log.debug('logout: deleted %s' % str(key))
    
    # sanity checks
    rv = True
    for key in (logout_func,):
        if key in request.environ:
            rv = request.environ[key]()
            assert rv == None, 'fatal error deleting session!'

    # Delete beaker cache session
    if session_key in request.environ:
        Session = request.environ[session_key]
        Session.delete()
        log.debug('Beaker session deleted!')

    # Delete paste artefacts
    if 'paste.cookies' in request.environ:
        request.environ['paste.cookies'] = []
        log.debug('Paste cookies deleted!')

    return HTTPRedirectResponse(urlto)


def login(request, template_name='auth/login.mako', redirect_field_name='next',
    login_form=None, ssl=False):
    """Main login view for authentication and authorization of remote users
    using cookie-based middleware and secret key. 

    See ``notmm.controllers.auth.AuthkitController`` for more details.
    """
    path_info = request.environ['PATH_INFO']
    redirect_to = request.GET.get(redirect_field_name, path_info)
    server_name = request.environ['SERVER_NAME']
    server_port = request.environ['SERVER_PORT']
    netloc = server_name + ":" + server_port + redirect_to
    redirect_to = 'http://' + netloc
    data = dict(login_form=forms.LoginForm(), action=path_info, msg=None)
    if request.method == 'POST':
        # authenticate/authorize the user if POST
        #assert isinstance(request.POST, dict), 'POST data not properly serialized!'

        form = forms.LoginForm(request.POST.copy())
        if form.is_valid():
            # basic form validation was ok
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                authenticate_user(request, username, password) 
            except NotAuthenticatedError:
                data['msg'] = 'Username or password incorrect. Please try again.'
            else:
                return HTTPRedirectResponse(redirect_to)
    
    # User is already authenticated or is using GET to access the 
    # login screen.
    return direct_to_template(request, template_name, extra_context=data)

def unauthorized(request):
    '''Denies access middleware to unauthorized users'''
    # Only registered accounts may create blog entries
    from notmm.utils.wsgilib import HTTPUnauthorized
    message = '''\
<html>
<head>
 <title>Permission denied</title>
</head>
<body>
<h2>Permission denied</h2>
<p>Please <a href="/session_login/">authenticate</a> first. Anonymous blog
posting is not permitted yet. A valid account is required to post new articles.
</p>
<p>Thanks for your understanding and have fun writing stuff... :)</p>
</body>
</html>
    '''
    return HTTPUnauthorized(message , mimetype='text/html')

