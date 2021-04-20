import time
import hashlib
import logging

#from pubsub import pub
#import beaker.session
#from notmm.utils.configparse import loadconf
from notmm.utils.wsgilib     import HTTPRedirectResponse
#from notmm.controllers.auth  import AuthCookieController

from notmm.utils.template    import direct_to_template
from authkit.authenticate   import valid_password
from authkit.permissions    import RemoteUser
from authkit.authorize      import NotAuthenticatedError

log = logging.getLogger(__name__)
#auth_conf = loadconf('development.ini', section='authkit')

__all__ = ['authenticate_user', 'logout', 'login', 'unauthorized']

def authenticate_user(request, username, password, tokens='', user_data=time.ctime,
    authfunc='paste.auth_tkt.set_user'):
    """Authenticate the user into the site and update the last_modified
    timestamp if authentication and authorization granted user access."""

    # Add the cookie middleware
    # secret = hashlib.md5(username).hexdigest()
    # request = AuthTKTMiddleware(request, secret)
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
    session_key='wsgioauth2.session', urlto='/'):
    if 'REMOTE_USER' in request.environ.keys():
        del request.environ['REMOTE_USER']
        log.debug('Session logout: deleted REMOTE_USER from session!')
    if 'HTTP_COOKIE' in request.environ.keys():
        del request.environ['HTTP_COOKIE']
        log.debug('deleted HTTP_COOKIE')
    return HTTPRedirectResponse(urlto)


def login(request, template_name='auth/login.mako', redirect_field_name='next',
    login_form=None, ssl=False):
    """Main login view for authentication and authorization of remote users
    using cookie-based middleware and secret key. 

    See ``notmm.controllers.auth.AuthkitController`` for more details.
    """
    log.debug("in login view...")
    return HTTPRedirectResponse('/')
    
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

