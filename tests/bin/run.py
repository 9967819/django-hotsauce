#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the django-hotsauce distribution.
# Please see the "LICENSE" file for details.

import sys
import os
import argparse

# Hack for adding lib/sandbox to the pythonpath
currentdir = os.environ['ROOTDIR']
confdir = os.environ.get('CONFDIR', os.path.join(currentdir, 'etc'))
testdir = os.environ['TESTDIR']
sys.path.append(os.path.join(currentdir, 'lib')) # test apps
sys.path.append(os.path.join(currentdir, 'lib/site-packages')) # contrib apps

#if not 'django' in sys.modules.keys():
#    sys.path.append(os.environ['DJANGO_HOME'])


# examples and contrib apps
vpath = (
    os.path.join(currentdir, '../examples/lib'),
    #os.path.join(currentdir, '../examples/contrib'),
    os.path.join(currentdir, '../examples/lib/site-packages')
    ) 
for path in vpath:
    sys.path.append(path)

from djangohotsauce.utils.testlib import SimpleTestRunner
from djangohotsauce.utils.configparse import loadconf

# TODO: Add "-c config.ini" support using getopt
testdir = confdir
app_conf = loadconf(os.path.join(testdir, 'development.ini'))
default_modules = ['auth','apps','datastore','dbapi','wsgi','utils','django110']
def parse_command_line(argv=sys.argv):
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('-v', '--verbose', \
        dest="verbose", \
        action="store_true", \
        help="Enable maintainer mode", \
        default=False
        )
    # $DJANGO_CONF 
    parser.add_argument('-c', '--config', \
        dest="app_conf", \
        nargs=1, \
        help="Path to a alternative development.ini (Default: $DJANGO_CONF)",
        default=os.path.join(currentdir, "development.ini")
        )
    # $DJANGO_SETTINGS_MODULE    
    parser.add_argument('--settings', \
        dest="settings", \
        nargs=1, \
        required=False, \
        help="Django settings module (Default: $DJANGO_SETTINGS_MODULE)", \
        default=os.environ['DJANGO_SETTINGS_MODULE']
        )
    # Adds support for $PYTHONPATH overriding
    parser.add_argument('--pythonpath', \
        dest="vpath",   \
        default=vpath, \
        required=False, 
        )
    parser.add_argument('-C', '--collections', 
        dest="collections", \
        type=str, \
        required=False, \
        default=default_modules,
        help="List of subpackages to search for test scripts"
        )
    
    #interactive option here

    options = parser.parse_args(args=argv[1:])
    return options

def main(verbosity=1):
    options = parse_command_line()
    if options.verbose:
        verbosity = 2
    runner = SimpleTestRunner(options, verbosity=verbosity)
    runner.run()

if __name__ == '__main__':
   main()


