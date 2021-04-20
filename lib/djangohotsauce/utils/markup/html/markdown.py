#!/usr/bin/env python
# Copyright (c) 2007-2019 Jack Bortone
# All rights reserved.
"""
Markdown2 utils

"""
import sys
PY3K = sys.version_info[0] == 3

if PY3K:
    from ._markdown3 import Markdown, MarkdownError
else:
    from ._markdown2 import Markdown, MarkdownError

__all__ = ['convert2markdown']

   
def convert2markdown(value, ispath=False):
    """Transform a markdown string into valid HTML markup. 
    
    ``ispath`` -- Indicates that ``value`` should be treated as a Unix pathname.
    """

    try:
        if ispath is not False:
            with open(value, 'r') as f:
                value = f.read()
                f.close()
        # Convert the string to html
        md = Markdown()
        html_obj = md.convert(value)
    except MarkdownError as e:
        # Error converting the document to html
        raise e
    else:
        return html_obj

#convert_to_markdown = convert2markdown
