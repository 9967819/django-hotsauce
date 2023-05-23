
def redirect(self, url, start_response, headers={}):
    h = {'Content-Type': 'text/html; charset=utf-8', 'Location': url}
    h.update(headers)
    start_response('307 Temporary Redirect', list(h.items()))
    e_url = html.escape(url).encode('iso-8859-1')
    yield b'<!DOCTYPE html>'
    yield b'<html><head><meta charset="utf-8">'
    yield b'<meta http-equiv="refresh" content="0; url='
    yield e_url
    yield b'"><title>Redirect to '
    yield e_url
    yield b'</title></head><body><p>Redirect to <a href="'
    yield e_url
    yield b'">'
    yield e_url
    yield b'</a>&hellip;</p></body></html>'

