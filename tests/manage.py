#!/usr/bin/env python
"""manage.py script to perform management tasks"""

import sys,os
import django


# Hack for adding lib/sandbox to the pythonpath
currentdir = os.getcwd()

sys.path.append(os.path.join(currentdir, 'lib')) # test apps
sys.path.append(os.path.join(currentdir, 'lib/site-packages')) # contrib apps


def setup_environ():
    """Environment sanity checks"""
    required_keys = ('DJANGO_HOME', 'DJANGO_SETTINGS_MODULE')
    for name in required_keys:
        if not os.environ.has_key(name):
            # Raise an error since this is a requirement
            raise EnvironmentError('Please set %r' % name)
        else:
            print 'Found %s .. ok' % repr(name)
    # Add `DJANGO_HOME` to sys.path
    sys.path.append(os.environ['DJANGO_HOME'])

def init_main(argv=None, fallback='settings'):
    """A wrapper for execute_manager"""
    try:
        setup_environ()
        
        #module_name  = os.environ['DJANGO_SETTINGS_MODULE'] or fallback
        #settings_module = __import__(module_name, {}, {}, [])

    except (ImportError, EnvironmentError), e:
        raise e
    else:
        from notmm.dbapi.orm import management
        management.execute_from_command_line(argv)

if __name__ == "__main__":
    #django.setup()
    init_main(argv=sys.argv)

