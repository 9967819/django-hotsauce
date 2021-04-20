"""New-style configuration variables should go in this file.

Once again, we're taking another route, but not reinventing any
wheel. 

To retain the original Django configuration scheme, use the 
following import statement ::

    >>> from configuration import settings 

In short, YMMV...

"""
from notmm.utils.django_settings import SettingsProxy

settings = SettingsProxy(autoload=True).get_settings()
settings.PROJECT_NAME = 'MightyHelloWorldApp'

__all__ = ('settings', )

