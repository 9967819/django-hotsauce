#!/usr/bin/env python
import os
import sys

from kiwi.dist import setup, listfiles, listpackages

from gazpacho import __version__

templates = []
data_files = [
    ('share/doc/gazpacho', ('AUTHORS', 'ChangeLog', 'CONTRIBUTORS',
                            'COPYING', 'README', 'NEWS')),
    ('share/doc/gazpacho/examples', listfiles('examples', '*')),
    ('$datadir/catalogs', listfiles('catalogs', 'base.xml')),
    ('$datadir/pixmaps', listfiles('pixmaps', '*.png')),
    ('$datadir/pixmaps', listfiles('pixmaps', '*.ico')),
    ('$datadir/resources/base', listfiles('resources', 'base', '*.png')),
    ('$datadir/glade', listfiles('glade', '*.glade')),
    ]

def list_plugins():
    ret = []
    for dir in os.listdir('plugins'):
        dest = '$datadir/plugins/%s' % dir
        files1 = listfiles(os.path.join('plugins', dir), '*.plugin')
        if files1:
            ret.append((dest, files1))
        files2 = listfiles(os.path.join('plugins', dir), '*.py')
        if files2:
            ret.append((dest, files2))
    return ret

data_files.extend(list_plugins())

resources = dict(locale='$prefix/share/locale')
global_resources = dict(
    doc='$prefix/share/doc/gazpacho',
    pixmap='$datadir/pixmaps',
    glade='$datadir/glade',
    resource='$datadir/resources',
    catalog='$datadir/catalogs',
    plugins='$datadir/plugins')

# When building the installer, install some extra stuff.
kwargs = {}
if 'bdist_wininst' in sys.argv:
    import shutil
    src = os.path.join('bin', 'gazpacho')
    shutil.copy2(src, os.path.join('bin', 'launch-gazpacho.py'))
    shutil.copy2(src, os.path.join('bin', 'launch-gazpacho.pyw'))
    scripts = ['bin/launch-gazpacho.py',
               'bin/launch-gazpacho.pyw']
elif 'py2exe' in sys.argv:
    import py2exe
    scripts = []
    kwargs['windows'] = [dict(script='bin/gazpacho',
                              icon_resources=[(1, 'gazpacho.ico')]
                              )]
    kwargs['options'] = dict(py2exe=dict(
        packages='encodings',
        includes=('kiwi,cairo,pango,pangocairo,atk,gobject,win32com')))
    import shutil
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.mkdir('dist')
    shutil.copytree('glade', 'dist/glade')
    shutil.copytree('pixmaps', 'dist/pixmaps')
    shutil.copytree('catalogs', 'dist/catalogs')
    shutil.copytree('resources', 'dist/resources')
else:
    scripts = ['bin/gazpacho']
    templates.append(('share/applications',
                      ['gazpacho.desktop']))

setup(name='gazpacho',
      version=__version__,
      description='GTK+ GUI Designer',
      author='SICEm S.L.',
      author_email='lgs@sicem.biz',
      url='http://gazpacho.sicem.biz',
      license='LGPL',
      packages=listpackages('gazpacho'),
      scripts=scripts,
      data_files=data_files,
      resources=resources,
      global_resources=global_resources,
      templates=templates,
      **kwargs)

if 'bdist_wininst' in sys.argv:
    for script in scripts:
        os.unlink(script)
