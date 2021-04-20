import tidylib

def clean_html_document(html, opts={}, keep_doc=True):
    """Clean a HTML document using the tidylib module
    
    Returns a 2-items tuple with cleaned html fragment at position 0
    and validation errors at position 1. May also accept custom tidy options
    passed as keyword arguments. 
    """
    html, errors = tidylib.tidy_document(html, opts, keep_doc=keep_doc)
    return (html, errors) 
