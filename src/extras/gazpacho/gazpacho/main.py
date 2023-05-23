# Copyright (C) 2004,2005 by SICEm S.L.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import optparse
import os
import sys

from gazpacho import __version__
from gazpacho.i18n import _

PYGTK_REQUIRED = (2, 6, 0)
KIWI_REQUIRED = (1, 9, 6)

def open_project(app, filename, profile):
    if not profile:
        return app.open_project(filename)

    print('profiling')
    import hotshot
    from hotshot import stats
    prof = hotshot.Profile("gazpacho.prof")
    prof.runcall(app.open_project, filename)
    prof.close()

    s = stats.load("gazpacho.prof")
    s.strip_dirs()
    s.sort_stats('time', 'calls')
    s.print_stats(25)

def run_batch(app, command):
    ns = dict(new=lambda w: app.create(w))
    eval(command, {}, ns)

def run_console(app):
    try:
        import readline
        import rlcompleter
        assert rlcompleter
        readline.parse_and_bind('tab: complete')
    except ImportError:
        pass

    import code
    ia = code.InteractiveConsole(
        locals=dict(project=app.get_current_project()))
    ia.interact()

def check_deps(debug=False):
    # PyGTK
    if debug:
        print('Importing PyGTK...')

    try:
        import gtk
        gtk # stuid pyflakes
    except ImportError:
        try:
            import pygtk
            # This modifies sys.path
            pygtk.require('2.0')
            # Try again now when pygtk is imported
            import gtk
        except ImportError:
            raise SystemExit("PyGTK is required to run Gazpacho")

    import gobject
    if (os.path.dirname(os.path.dirname(gtk.__file__)) !=
        os.path.dirname(gobject.__file__)):
        print ('WARNING: GTK+ and GObject modules are not loaded from '
               'the same prefix')

    if debug:
        print('Python:\t', '.'.join(map(str, sys.version_info[:3])))
        print('GTK+:\t', '.'.join(map(str, gtk.gtk_version)))
        print('PyGTK:\t', '.'.join(map(str, gtk.pygtk_version)))

    if gtk.pygtk_version < PYGTK_REQUIRED:
        raise SystemExit("PyGTK 2.6.0 or higher required to run Gazpacho")

    if gtk.pygtk_version >= (2, 7, 0):
        if gtk.pygtk_version < (2, 8, 0):
            raise SystemExit("PyGTK 2.7.x is not supported, upgrade to 2.8.0")

        if debug:
            print('Using PyGTK 2.8.x, ignoring deprecation warnings')

        # Ignore deprecation warnings when using 2.7.x
        import warnings
        warnings.filterwarnings('ignore', category=DeprecationWarning)

    # kiwi
    if debug:
        print('Importing kiwi...')

    try:
        from kiwi.__version__ import version
    except ImportError:
        raise SystemExit("kiwi is required to run Gazpacho")

    if version < KIWI_REQUIRED:
        raise SystemExit("kiwi %s or higher is required" %
                         '.'.join(map(str, KIWI_REQUIRED)))

def setup_app(testsuite=False):
    pass

def show(options, filenames=[]):
    import gtk
    from gazpacho.catalog import load_catalogs
    load_catalogs()
    from gazpacho.loader.loader import ObjectBuilder

    if not filenames:
        raise SystemExit('--show needs at least one filename')

    windows = []
    def window_close_cb(window, event):
        windows.remove(window)
        if not windows:
            gtk.main_quit()

    for filename in filenames:
        builder = ObjectBuilder(filename)
        for widget in builder.get_widgets():
            if not isinstance(widget, gtk.Window):
                continue
            elif isinstance(widget, gtk.Action):
                if widget.get_property('stock-id') == gtk.STOCK_QUIT:
                    widget.connect('activate', gtk.main_quit)
            widget.connect('delete-event', window_close_cb)
            widget.show_all()
            windows.append(widget)

    if not windows:
        raise SystemExit("none of the specified files has any windows")

    gtk.main()

def debug_hook(exctype, value, tb):
    import traceback

    traceback.print_exception(exctype, value, tb)
    print()
    print('-- Starting debugger --')
    print()
    import pdb
    pdb.pm()
    raise SystemExit

def launch(options, filenames=[]):
    if options.debug:
        print('Loading gazpacho')

    # Delay imports, so command line parsing is not slowed down
    from kiwi.component import provide_utility
    from gazpacho.interfaces import IGazpachoApp, IPluginManager
    from gazpacho.app.app import Application
    from gazpacho.app.debugwindow import DebugWindow, show
    from gazpacho.plugins import PluginManager

    plugin_manager = PluginManager()
    provide_utility(IPluginManager, plugin_manager)

    gazpacho = Application()
    provide_utility(IGazpachoApp, gazpacho)

    if options.debug:
        sys.excepthook = debug_hook
    else:
        DebugWindow.application = gazpacho
        sys.excepthook = show

    for filename in filenames:
        if not os.path.exists(filename):
            raise SystemExit('%s: no such a file or directory' % filename)

        if not os.access(filename, os.R_OK):
            raise SystemExit('Could not open file %s: Permission denied.' %
                             filename)
        open_project(gazpacho, filename, options.profile)

    if options.update:
        for project in gazpacho.get_projects():
            project.save(project.path)

        return

    # If no filenames were specified, open up an empty project
    if not filenames:
        gazpacho.new_project()

    if options.batch:
        run_batch(gazpacho, options.batch)
        return
    elif options.console:
        run_console(gazpacho)
        return

    if options.debug:
        print('Running gazpacho')

    gazpacho.run()

def main(args=[]):
    parser = optparse.OptionParser(version=__version__)
    parser.add_option('', '--profile',
                      action="store_true",
                      dest="profile",
                      help=_("Turn on profiling support"))
    parser.add_option('', '--debug',
                      action="store_true",
                      dest="debug",
                      help=_("Turn on pdb debugging support"))
    parser.add_option('', '--batch',
                      action="store",
                      dest="batch",
                      help=_("Batch command"))
    parser.add_option('-u', '--update',
                      action="store_true",
                      dest="update",
                      help=_("Load glade file and save it"))
    parser.add_option('-c', '--console',
                      action="store_true",
                      dest="console",
                      help=_("Start up a console"))
    parser.add_option('-s', '--show',
                      action="store_true",
                      dest="show",
                      help=_("Only open and display the interface"))

    # Until we can use GOptionParser
    args = args[:]
    if '--g-fatal-warnings' in args:
        args.remove('--g-fatal-warnings')

    options, args = parser.parse_args(args)

    if options.batch or options.console:
        options.debug = True

    filenames = []
    if len(args) >= 2:
        filenames = [os.path.abspath(name) for name in args[1:]]

    # Do this before importing application, which imports gtk
    check_deps(debug=options.debug)
    setup_app()

    if options.show:
        show(options, filenames)
    else:
        launch(options, filenames)
