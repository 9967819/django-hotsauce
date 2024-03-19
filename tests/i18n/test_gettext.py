#!/usr/bin/env python
#from django.utils.translation.trans_real import DjangoTranslation
from django.middleware.locale            import LocaleMiddleware
from notmm.controllers.wsgi              import WSGIController
from notmm.utils.wsgilib                 import HTTPResponse
from notmm.utils.django_settings import LazySettings

from test_support                        import *

import gettext

class Translation(object):
    """
    The purpose of this class is to store the actual translation function upon
    receiving the first call to that function. After this is done, changes to
    ``USE_I18N`` will have no effect to which function is served upon request. If
    your tests rely on changing ``USE_I18N``, you can delete all the functions
    from _trans.__dict__.

    Note that storing the function with setattr will have a noticeable
    performance effect, as access to the function goes the normal path,
    instead of using __getattr__.
    """

    def __init__(self, app_label):
        self.app_label = app_label

    def __getattr__(self, real_name):


        if settings.USE_I18N:
            from django.utils.translation import trans_real as trans
            # Uncomment to enable new LOCALE_PATHS behavior 
            #project = import_module(self.app_label)
            #project_locale_path = path.normpath(
            #    path.join(path.dirname(project.__file__), 'locale'))
            #
            # Make sure the project's locale dir isn't in LOCALE_PATHS
            # normalized_locale_paths = [path.normpath(locale_path)
            # for locale_path in settings.LOCALE_PATHS]
            #    if (path.isdir(project_locale_path) and
            #    not project_locale_path in normalized_locale_paths):
            #        warnings.warn("Translations in the project directory "
            #                      "aren't supported anymore. Use the "
            #                      "LOCALE_PATHS setting instead.",
            #                      PendingDeprecationWarning)
        else:
            from django.utils.translation import trans_null as trans
        setattr(self, real_name, getattr(trans, real_name))
        return getattr(trans, real_name)

class I18NLocaleManager(Translation):
    pass

class I18NLocaleManagerTestCase(unittest.TestCase):
    
    LocaleManager = I18NLocaleManager

    def setUp(self):
        pass

    def test_ugettext_lazy(self):
        locale = self.LocaleManager('sandbox')
        _ = locale.gettext
        #print _('hello world')
        self.assertEqual(callable(_), True)
        self.assertRaises(TypeError, _, 1234, 'expected a string value!')
        t1 = _('hello world')
        self.assertEqual(t1, unicode('hello world'), 'expected a unicode type object!')
