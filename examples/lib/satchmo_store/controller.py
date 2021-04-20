from django.core.handlers.wsgi import WSGIHandler

class SatchmoController(WSGIHandler):
    def __init__(self, *args, **kwargs):
        super(SatchmoController, self).__init__()

