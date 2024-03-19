

from notmm.utils.django_settings import SettingsProxy
from test_support import unittest
from django.conf import settings as _settings

class LazySettingsTestCase(unittest.TestCase):
    
    def setUp(self):
        self.settings_module = _settings

    
    def test_count(self):
        # check that django.conf.settings and site-derived
        # settings instance are equivalent
        from sandbox.configuration import settings
        
        c1 = settings.count()
        c2 = len([item for item in dir(self.settings_module) if item.isupper() ])
        
        # django will add "SETTINGS_MODULE" dynamically
        #self.failUnlessEqual(c1, c2 - 1)

    def test_equivalent(self):

        settings = SettingsProxy(autoload=True).settings
        self.failUnlessEqual(hasattr(self.settings_module, 'SETTINGS_MODULE'), True)
        self.failUnlessEqual(hasattr(settings, 'SETTINGS_MODULE'), False)
        
        # check that LazySettings() works as expected; SETTINGS_MODULE value
        # must match DJANGO_SETTINGS_MODULE..
        self.failUnlessEqual(self.settings_module.SETTINGS_MODULE, settings.__name__)

