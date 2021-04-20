from notmm.utils.configparse     import string_getter
from notmm.utils.template        import *
from test_support import unittest, app_conf, settings

import posixpath

class TemplateLoaderFactoryTestCase(unittest.TestCase):
    
    def setUp(self):
        TemplateLoaderFactory.configure(
            kwargs={'directories': settings.TEMPLATE_DIRS, 
                    'cache_enabled': settings.ENABLE_BEAKER})
        self.loader = TemplateLoaderFactory.get_loader()
        

    def test_get_template_loader(self):
        # parent class must match the expected templates backend
        loader = self.loader
        
        #self.assertEqual(isinstance(self.loader, TemplateLoader), True)
    
        # See if this loader has defined minimal hooks
        self.assertEqual(hasattr(loader, 'get_template'), True)
        self.assertEqual(hasattr(loader, 'has_template'), True)

class TemplateLoaderTestCase(TemplateLoaderFactoryTestCase):

    def test_get_template(self):
        # Find a relative template by name
        t = 'sandbox/request_context.mako'
        template = self.loader.get_template(t)
        uri = template.uri
        self.assertEqual(uri, t)
        self.assertEqual(self.loader.has_template(uri), True)
        
        head, tail = posixpath.split(uri)
        self.assertEqual(head, 'sandbox')
        self.assertEqual(posixpath.basename(template.filename), tail)

        # available templates directories 
        self.assertEqual(len(self.loader.directories)>=1, True)
    
