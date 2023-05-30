#!/usr/bin/env python
# -*- coding: utf-8 -*-

class HTTPException(BaseException):
    status_int = 500
    use_etags = False

HTTPServerError = HTTPException

class HTTPNotModified(HTTPException):
    status_int = 304
class HTTPClientError(HTTPException):
    status_int = 400 # bad request
class HTTPUnauthorized(HTTPClientError):
    status_int = 401
class HTTPAuthenticationError(HTTPClientError):
    status_int = 403
class HTTPNotFound(HTTPException):
    """HTTP 404 (Not Found)"""
    status_int = 404
HTTPNotFoundResponse = HTTPNotFound    
HTTPForbidden = HTTPAuthenticationError    
