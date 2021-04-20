from djangohotsauce.utils.django_settings import LazySettings
from djangohotsauce.utils.django_compat import get_callable
from importlib import import_module

class ContextPopException(Exception):
    "pop() has been called more times than push()"
    pass

class RequestContext(object):
    def __init__(self, request, ctx):

        self.settings = LazySettings()
        self.context_processors = self.settings.TEMPLATE_CONTEXT_PROCESSORS
        self.view_dicts = [ctx,]
        for name in self.context_processors:
            f = get_callable(name)
            result = f(request)
            self.view_dicts.append(result)

    def __getitem__(self, key):
        for d in reversed(self.view_dicts):
            if key in d:
                return d[key]
        raise KeyError(key)

    def update(self, dct):
        self.view_dicts.append(dct)
        return None
        
    def pop(self):
        if len(self.view_dicts) == 1:
            raise ContextPopException
        return self.view_dicts.pop()

   

