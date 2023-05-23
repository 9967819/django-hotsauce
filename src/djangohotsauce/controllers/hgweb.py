#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""BaseMercurialController 1.0.2 extension"""
import sys
import os
import os.path
from djangohotsauce.utils.log import configure_logging
from djangohotsauce.controllers.wsgi import WSGIController

log = configure_logging('BaseMercurialController')

# enable demandloading to reduce startup time
from mercurial import demandimport; 
demandimport.enable()

from mercurial.hgweb.hgwebdir_mod import hgwebdir
from mercurial.hgweb.request import wsgiapplication

# Uncomment to send python tracebacks to the browser if an error occurs:
#import cgitb
#cgitb.enable()

# If you'd like to serve pages with UTF-8 instead of your default
# locale charset, you can do so by uncommenting the following lines.
# Note that this will cause your .hgrc files to be interpreted in
# UTF-8 and all your repo files to be displayed using UTF-8.

_default_encoding = 'utf-8'
_enable_gzip = True
_enable_ssl_transport = True

#if sys.version_info[0] == 2:
#    sys.setdefaultencoding(_default_encoding)

# The config file looks like this.  You can have paths to individual
# repos, collections of repos in a directory tree, or both.
#
# [paths]
# virtual/path = /real/path
# virtual/path = /real/path
#
# [collections]
# /prefix/to/strip/off = /root/of/tree/full/of/repos
#
# collections example: say directory tree /foo contains repos /foo/bar,
# /foo/quux/baz.  Give this config section:
#   [collections]
#   /foo = /foo
# Then repos will list as bar and quux/baz.
#
# Alternatively you can pass a list of ('virtual/path', '/real/path') tuples
# or use a dictionary with entries like 'virtual/path': '/real/path'

__all__ = ['BaseMercurialController']


class BaseMercurialController(WSGIController):

    def __init__(self, **kwargs):
        self._default_encoding = _default_encoding
        super(BaseMercurialController, self).__init__(**kwargs)
        self.settings.APPEND_SLASH = False

    def init_request(self, environ):
        if not 'hgweb.config' in environ:
            if not 'ROOTDIR' in environ:
                environ['ROOTDIR'] = os.environ.get('ROOTDIR')
            environ['hgweb.config'] = os.path.join(
                environ['ROOTDIR'], 'etc/hgweb.config'
            )
        if not 'HGENCODING' in environ:
            environ["HGENCODING"] = self._default_encoding
        self._request = self._request_class(environ)
        log.debug(self._request)
        return self._request

    def _make_web_app(self, config):
        log.debug(config)
        return hgwebdir(config)

    ### uwsgi-specific handlers.py using uwsgi socket (ssl/tls)
    ### BaseTLSController 
    def _uwsgi_handle_clone(self, request):
        request = self.init_request(request.environ)
        self._config = request.environ["hgweb.config"]
        try:
            response = self._make_web_app(self._config)
        except Exception:
            return self.handle500(request)
        else:
            return response

    def application(self, environ, start_response):
        response = self._uwsgi_handle_clone(environ, start_response)
        return self._response_class(response)
