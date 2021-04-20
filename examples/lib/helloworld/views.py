import posixpath
import io

from notmm.utils.wsgilib import HTTPResponse
from .configuration import settings

def image_handler(request, *args, **kwds):
    docroot = kwds.get('document_root', settings.MEDIA_ROOT)
    filename = posixpath.split(request.path_url)[-1]
    ext = filename.split('.')[-1]

    filename = posixpath.join(docroot, filename)

    fdata = io.open(filename, 'rb')
    outbuf = fdata.read()
    headers = (
      ('Content-Type', "image/%s" % ext),
      ('Content-Length', str(len(outbuf)))
    )
    return HTTPResponse(content=outbuf, headers=headers, force_unicode=False)

