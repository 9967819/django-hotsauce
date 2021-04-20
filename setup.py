#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
PY3K = sys.version_info[0] == 3
import os
import posixpath
import glob

from setuptools import setup, find_packages

workdir = os.getcwd()
admindir = posixpath.join(workdir, 'admin')
staticdir = posixpath.abspath(os.path.join(admindir, 'static'))

#from pkg_resources import resource_stream
# Do import buildutils commands if available!
#try:
#    import buildutils
#except ImportError:
#    print('Consider installing the buildutils module!')

scripts_data = ['tools/httpserver.py']

classifiers = [
    (str(item)) for item in open(posixpath.abspath(os.path.join(staticdir, \
    'classifiers.txt'))).read().split('\n') if item != '']

setup(
    name='django-hotsauce',
    version='1.3.7',
    description='Scalable and heterogeneous web toolkit sitting on top of Django and others',
    long_description='The Django-hotsauce programming toolkit is a high-performance and scalable Python web framework derived from Django project.',
    author='Jack Bortone',
    author_email='jack@open-neurosecurity.org',
    license='Apache License V2',
    keywords='django-hotsauce, django, uwsgi, oauth, werkzeug',
    #url='https://isotopesoftware.ca/software/django-hotsauce',
    #maintainer=meta['Maintainer'],
    #maintainer_email=meta['Maintainer-email'],
    scripts=scripts_data,

    # Include stuff which belong in SVN or mentioned in MANIFEST.in
    include_package_data=False,

    # Location where packages lives
    package_dir={'':'lib'},
    packages=find_packages('lib'),
    # Package classifiers are read from static/classifiers.txt
    classifiers=classifiers,

    # Add Cython compiled extensions
    #cmdclass={'build_ext': build_ext},
    #ext_modules=ext_modules,
    
    # Minimal packages required when doing `python setup.py install`.
    install_requires=[
        #'Django>=1.11.17',  # Maintainers should not need this :-)
        'pytz>=2017.2',     # django dependency (optional)
        #'Beaker>=1.9.0',    # memcached support (optional)
        #'configobj>=4.7.2', # in djangohotsauce.utils.configparse (required)
        'argparse>=1.1',    # Used by tools/httpserver.py (required)
        #'demjson>=2.2.4',   # JSON support (optional)
        'Mako>=1.1.0',      # Mako template backend (optional)
        #'feedparser>=5.1.2'# RSS 2.0 parsing (optional)
        #'docutils>=0.8.1',         # Docutils support (optional)
        #'python-epoll>=1.0',       # For epoll support Linux only (optional)
        #'pytidylib>=0.2.1',        # PyTidyLib support      (optional) 
        #'python-memcached>=1.58',  # memcached support      (optional)
        'werkzeug>=1.0.1',         # Werkzeug  support      (optional) 
        #'gevent==1.4.0',            # Gevent    support      (optional)
        #'ZODB>=5.3.0',              # ZODB backend support   (optional)
        #'ZEO>=5.1.0',               # ZEO backend support    (optional)
        #'Elixir>=0.7.1',            # Elixir support         (optional)
        #'libschevo>=4.1',         # Schevo backend support (required)
        #'blogengine2>=0.9.6',       # BlogEngine 2.0 support (optional)
        'uWSGI>=2.0.18',          # uWSGI support          (required)
        #'transaction>=2.4',         # transaction support    (required)
        #'persistent>=4.4.3'         # persistence support    (required)
    ],
    zip_safe=False
)

