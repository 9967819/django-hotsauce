#!/usr/bin/env python
from django.utils.translation.trans_real import DjangoTranslation
from django.middleware.locale            import LocaleMiddleware
from notmm.controllers.wsgi              import WSGIController
from notmm.utils.wsgilib                 import HTTPResponse
from test_support                        import *

class I18NController(WSGIController):

    i18n_middlewares = (LocaleMiddleware, )
    response_class = HTTPResponse

    #def get_locale_manager(self):
    #    return getattr(self, 'locale_manager')()
    
    def get_response(self, path_url):
        wsgi_response = super(self.__class__, self).get_response(path_url)
        for mw in self.i18n_middlewares:
            self.i18n_process_middleware(mw, 'process_request')
            self.i18n_process_middleware(mw, 'process_response', wsgi_response)
        return wsgi_response

    def i18n_process_middleware(self, mw, funcname, response=None):
            
        if self.request is not None:
            #print 'processing middleware: %s'%middleware
            if not response:
                getattr(mw(), funcname)(self.request)
            else:
                getattr(mw(), funcname)(self.request, response)
                # setup the WSGI response
                response.language_code = response.http_headers['Content-Language']
                # install the translations here

class I18NControllerTestCase(BaseControllerTestCase):
    wsgi_app = I18NController
    
    #def setUp(self):
    #    pass
    
    def test_get_current_locale(self):
        res = self.client.get('/')
        self.failUnlessEqual(res.status==200, True, res.status)
        lang_code = res.language_code
        self.assertEqual(lang_code=='en-us', True)

