#!/usr/bin/env python2.5
"""manage.py script to perform management tasks"""

import sys,os

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
        module_name  = os.environ['DJANGO_SETTINGS_MODULE'] or fallback
        settings_module = __import__(module_name, {}, {}, [])
        #settings_module = sys.modules[module_name]

    except (ImportError, EnvironmentError), e:
        raise e
    else:
        from django.core.management import execute_from_command_line
        execute_from_command_line(argv)

if __name__ == "__main__":
    init_main(argv=sys.argv)

