#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Mostly Random WSGI Utilities.

"""
import sys
import socket, hashlib
from djangohotsauce.utils.log import configure_logging
from djangohotsauce.release import VERSION, RELEASE_NAME

log = configure_logging(__name__)
PY3K = sys.version_info[0] == 3

if PY3K:
    from http.client import responses
    from http.cookies import SimpleCookie
else:
    import platform
    log.debug("CPython (%s) WSGI 1.0 environment detected." % platform.python_implementation())
    from httplib import responses
    from Cookie import SimpleCookie

from werkzeug.datastructures import Headers as ResponseHeaders

def bytearray2str(obj, mode='replace'):
    obj.decode('utf8', errors=mode)
    return obj

def sniff_content_encoding(s, default='utf-8'):
    """
    Attempts to detect the character set of a string value ``s`` or 
    ``default`` if the ``chardet`` module is not found.

    """
    try:
        import chardet
        content_encoding = chardet.detect(s)['encoding']
    except (ImportError, UnicodeDecodeError):
        content_encoding = default
    return content_encoding

def format_status_int(status_int):
    """
    Returns a string like "200 OK" if the status_int
    numeric value matches something in our internal
    map.
    
    """
    try:
        status_code = responses[int(status_int)]
    except (TypeError, KeyError):
        status_code = responses[500]    
    
    return "%s %s" % (status_int, status_code)

class BaseResponse(object):
    """
    A iterable WSGI object using a simple API inspired by Django
    ``HttpResponse``.
    
    >>>response = IterableWSGIResponse(content='hello world', mimetype='text/plain')
    """
    
    # default headers 
    headerClass = ResponseHeaders
    status_int = None
    #etag = None
    debug = False

    def __init__(
        self, content='', status=None, headers=None, mimetype='text/plain', 
        charset='utf-8', force_unicode=False, enable_cookies=False, 
        cache_timeout=600, etag=None, verbosity_level=0):
        """Create a new WSGI response instance.
        
        If ``force_unicode`` is set to ``False``, disable explicit
        multibyte conversion. (Binary files handlers may need this)
        """
        self.mimetype = mimetype
        self.charset = charset
        self.etag = etag

        if PY3K: # Python 3
            self.content = bytes(content, charset)
        else:    
            self.content = content.encode(charset)

        # Content-MD5 (for integrity checking of
        # the entity-body)
        self.content_hash = str(
	    hashlib.md5(content.encode(charset)).hexdigest()
	    )

        # Get the HTTP status code human representation. 
        if status is not None:
            self.status_code = format_status_int(status)
        else:
            # by default attempt to use status_int
            #assert isinstance(self.status_int, int)
            self.status_code = format_status_int(self.status_int)
        
        # Provides a basic HTTP/1.1 headers set
        self.cache_timeout = cache_timeout
        

        self.base_headers = [
           ('Content-Type', self.content_type),
           ('Content-Length', self.content_length),
           #('Content-MD5', self.content_hash),
           ('Cache-Control', 'max-age=%i' % self.cache_timeout),
           ('Server', "Django-hotsauce/%s (%s)" % (VERSION, RELEASE_NAME)),
        ]
    
        if self.etag is not None:
            self.http_headers['ETag'] = self.etag

        if headers is not None:
            if verbosity_level >= 2:
                log.debug("Headers found!")
            self.base_headers.extend(headers)
        
        self.http_headers = self.base_headers
        if enable_cookies:
            log.debug("warning: generic cookie support not implemented!")
            

    def __str__(self, skip_body=False):
        parts = [str(self.status)]
        parts += map('%s: %s'.__mod__, self.headers)
        if not skip_body and self.content != '':
            parts += ['', self.content]
        #outs = bytearray2str(bytearray(parts))
        return '\n'.join(parts)
    
    def __iter__(self):
        """Return a custom iterator type which iterates over the response."""  
        return iter([self.content])

    app_iter = property(__iter__)
    
    #__await__ = __iter__

    def __len__(self):
        """Return the Content-length value (type int)."""
         
        return len(self.content)
    
    def __getitem__(self, k):
        """For foo = response['foo'] operations"""
        try:
            v = self.http_headers[k]
        except KeyError:
            return None
        else:
            return v
    
    def __setitem__(self, item, value):
        """For response['foo'] = 'Bar' operations"""
        try:
            self.http_headers[item] = value
        except:
            raise
            
    content_length = property(__len__)
    
    def __call__(self, environ, start_response):
        if_none_match = environ.get('HTTP_IF_NONE_MATCH', None)
        
        if self.etag is not None and if_none_match == self.etag:
            start_response('304 Not Modified', [])
            return []
        else:
            #self.http_headers.add('ETag', self.etag)
            status_code = self.status_code
            start_response(status_code, self.headers)
            #assert isinstance(self.content, bytes)
            return self.app_iter

    def get_content_type(self):
        """Returns the current Content-type header"""
        return "%s; charset=%s" % (self.mimetype, self.charset)
    
    content_type = property(get_content_type)

    def write(self, text=''):
        """Writes characters (text) in the input buffer stream (body)"""
        if isinstance(text, str): 
            text.encode(self.charset)
        self.content += text
    
    def __next__(self):
        """ required method for being a proper iterator type """
        chunk = self.app_iter.__next__()

        #if isinstance(chunk, basestring):
        #    chunk.encode(self.charset)
        return chunk
    next = property(__next__)     
    
    def has_header(self, value):
        """ return True when ``value`` is found in self.headers (HTTP headers)
        """
        try:
            valueof = self.headers[value]
        except (KeyError, TypeError):
            return False
        else:
            return True
    
    @property        
    def headers(self):
        return [(hdr, str(val)) for hdr, val in self.http_headers]

    @property    
    def status(self):
        return self.status_int 

class HTTPFoundResponse(BaseResponse):
    """HTTP 302 (Found)
    
    Requires one param: 
    * location: a URI string.
    """
    status_int = 302
    
    def __init__(self, location, **kwargs):
        #kwargs['status'] = str(self.status_int)
        # Displays a short message to the user with a link to
        # the given resource URI
        # TODO: Use a template for this.
        kwargs['content'] = '''\
        <html>
        <p>Click here to follow this redirect: <a href=\"%s\">Link</a></p>
        </html>'''%location
        kwargs['mimetype'] = 'text/html'
        super(HTTPFoundResponse, self).__init__(**kwargs)
        
        #self.location = location     # location to redirect to

        #self.initial_kwargs = kwargs 
        self.http_headers.append(('Location', location)) #.split('?next=')[1]
        self.http_headers.append(('Cache-Control', 'no-cache')) # Prevent caching redirects

    def __call__(self, env, start_response):
        start_response(self.status_code, self.headers)
        return self.app_iter

HTTPRedirectResponse = HTTPFoundResponse # alias
HTTPResponse = BaseResponse

class HTTPSeeOtherResponse(HTTPFoundResponse):
    """HTTP 303 (See Other)"""
    status_int = 303

class HTTPNotModifiedResponse(HTTPResponse):
    """HTTP 304 (Not Modified)"""
    status_int = 304

    def __init__(self, *args, **kwargs):
        super(HTTPNotModifiedResponse, self).__init__(*args, **kwargs)
        
        self.http_headers['Date'] = datetime.now().ctime()
            

        del self.http_headers['Content-Type']
    
        self.content = '';


class HTTPUnauthorizedResponse(HTTPResponse):
    """HTTP 401 (Unauthorized)"""
    status_int = 401

class HTTPForbiddenResponse(HTTPResponse):
    """HTTP 403 (Forbidden)"""
    status_int = 403

class HTTPNotFoundResponse(HTTPResponse):
    status_int = 404
HTTPNotFound = HTTPNotFoundResponse
