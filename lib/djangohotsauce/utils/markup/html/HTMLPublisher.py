#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import posixpath
from time import gmtime, strftime
from docutils.core import publish_parts

__all__ = ('HTMLPublisher', )

#RestructuredTextPublisher
class HTMLPublisher(object):
    """ 
    HTML Publisher class supporting reStructuredText source input.
    """

    def __init__(self, source):
        if os.access(source, os.R_OK):
            self.instream = source
        elif isinstance(source, (basestring, str)): # handle UTF-8 and str types
            self.instream = source
        else:
            raise ValueError('Unrecognized source document: %r' % source)
  
        #self.metadata = self.getdocinfo(source)

        self.parts = None
 
    def getdocinfo(self, doc):
        """Return gmtime/mtime (unix timestamp) for ``doc``"""
        gmt = gmtime(posixpath.getmtime(doc))
        mtime = strftime("%Y/%m/%d", gmt)
        
        return (gmt, mtime)

    def render_to_html(self, keyname='html_body', writer_name='html'):
        """Renders the HTML element from the source document"""
        try:
            parts = publish_parts(source=self.instream, writer_name=writer_name)
        except KeyError:
            raise
        return parts[keyname]
        
    #ctx = dict(content=parts['html_body'], mtime=mtime)

