### Base request handler to implement a WSGI gateway 
from BaseHTTPServer import BaseHTTPRequestHandler

#### PyWebDAV imports
#import DAV
#import DAV.WebDAVServer
#DAV.WebDAVServer.DEBUG = True
####
# DAV server extention to implement DAV responses
# for published realms
from pywebdav.server.fileauth import DAVAuthHandler
####

####
# Front end controller script to integrate the DAV fileserver
# API 
from notmm.controllers.wsgi import WSGIController
from notmm.utils.wsgilib import HTTPRequest, HTTPResponse
####

#Local modules
#import settings
#import utils

# DAV10_CONFIG = getattr(settings, 'DAV10_CONFIG', {})
# Setup the filesystem-based provider :-)
# DAV10_IFACE_CLASS = settings.MOUNTPOINTS['test']['root']

class DAV10RequestHandler(BaseHTTPRequestHandler, DAVAuthHandler):
    
    server_software = "Python DAVserver/1.0 (WSGI version)"

    def __init__(self, *args, **kwargs):
        
        #self._config = None

        DAVAuthHandler.__init__(self, *args, **kwargs)


    def handle(self):
        DAVAuthHandler.handle(self)
    
class DAV10Controller(WSGIController):
    request_class = HTTPRequest
    response_class = HTTPResponse

    def application(self, environ, start_response):
        super(DAV10Controller, self).application(environ, start_response)


