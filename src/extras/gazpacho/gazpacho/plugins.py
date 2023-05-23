# Copyright (C) 2006 by Nokia Corporation
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

import configparser
import glob
import os
import sys

from kiwi.environ import environ
from kiwi.desktopparser import DesktopParser
from kiwi.python import namedAny

from gazpacho.config import get_app_data_dir
from gazpacho.i18n import _

class Plugin(object):
    """Base class for Gazpacho plugins"""

    def __init__(self, name):
        self.name = name

    def activate(self, app):
        """
        This method is called to initialize the plugin.

        It can be called at gazpacho startup time or when the user
        manually enables the plugin in the configuration dialog
        """

    def deactivate(self):
        """
        This method is called to shutdown a plugin

        It's called when the user disables a plugin in the configuration
        dialog
        """

    def get_configuration_dialog(self, parent_window=None):
        """
        If the plugin has configuration options it should return
        a dialog in this method
        """

class PluginInfoError(Exception):
    pass

class PluginInfo(object):
    """
    This class parses and stores the metada of a .plugin file for a Plugin.

    The format of such files is:

    [Gazpacho Plugin]
    name = plugin_name
    title = short human readable string
    class = plugin.dotted.class.name
    description = text description
    author = author name and e-mail
    version = plugin version
    """
    def __init__(self, filename):
        self._filename = filename
        self._parser = DesktopParser()
        self._parser.read(filename)

        if not self._parser.has_section('Gazpacho Plugin'):
            msg = "The plugin file %s should have a [Gazpacho Plugin] section"
            raise PluginInfoError(msg % filename)

        self.name = self._read_value('name')
        self.title = self._read_value('title', self.name)
        self.class_name = self._read_value('class')
        self.description = self._read_value('description',
                                            _('No description available'))
        self.author = self._read_value('author',
                                       _('No author available'))
        self.version = self._read_value('version',
                                        _('No version available'))

    def _read_value(self, key, default=None):
        ret = None
        try:
            ret = self._parser.get('Gazpacho Plugin', key)
        except configparser.NoOptionError:
            if default:
                ret = default
            else:
                msg = ("The plugin file %s should have a %s option" %
                       (self._filename, key))
                raise PluginInfoError(msg)
        return ret

class PluginManager(object):
    """
    See interfaces.IPluginManager
    """

    def __init__(self):
        # in this dictionary we save instances of PluginInfo objects
        # it is indexed by their names
        self._plugins = {}

        # here we save Plugin objects for those plugins that are activated
        self._activated_plugins = []

    def load_plugins(self):
        # first load user plugins
        user_dir = os.path.join(get_app_data_dir('gazpacho'), 'plugins')
        self.load_plugins_dir(user_dir)

        for system_dir in environ.get_resource_paths('plugins'):
            self.load_plugins_dir(system_dir)

    def load_plugins_dir(self, dirname):
        if not os.path.exists(dirname):
            return

        # search for a .plugin file in every subdir of dirname
        for plugin_dir in os.listdir(dirname):
            if not os.path.isdir(os.path.join(dirname, plugin_dir)):
                continue

            files = glob.glob(os.path.join(dirname,
                                              plugin_dir,
                                              '*.plugin'))
            if len(files) > 1:
                print(('warning: plugin dir %s has more than one .plugin '
                       'file. It will not be loaded' % plugin_dir))
            elif len(files) == 1:
                metadata_file = files[0]

                pi = PluginInfo(metadata_file)

                if pi.name in self._plugins:
                    print(('The plugin %s was already loaded. Skipping' %
                           metadata_file))

                self._plugins[pi.name] = pi

        # add it to the python path so we can load plugins later
        if dirname not in sys.path:
            sys.path.append(dirname)

    def get_plugins(self):
        return list(self._plugins.values())

    def is_activated(self, plugin_name):
        for plugin in self._activated_plugins:
            if plugin.name == plugin_name:
                return True
        return False

    def activate_plugins(self, plugin_names, app):
        for pn in plugin_names:
            self.activate_plugin(pn, app)

    def activate_plugin(self, plugin_name, app):
        if plugin_name not in list(self._plugins.keys()):
            raise PluginInfoError("There is no plugin with the name %s" %
                                  plugin_name)

        klass = None
        plugin_info = self._plugins[plugin_name]
        try:
            klass = namedAny(plugin_info.class_name)
        except AttributeError:
            raise PluginInfoError('Error while activating plugin %s. '
                                  'Check the "class" option in the %s.plugin '
                                  'file' % (plugin_name, plugin_name))
        except ImportError:
            raise PluginInfoError('Error while importing plugin %s. '
                                  'Check the plugin file is a valid python '
                                  'module/package' % plugin_name)

        if klass:
            plugin = klass(plugin_info.name)
            plugin.activate(app)
            self._activated_plugins.append(plugin)

    def deactivate_all(self):
        for plugin in list(self._activated_plugins):
            self._deactivate_plugin_internal(plugin)

    def _deactivate_plugin_internal(self, plugin):
        """
        Deactivate the especified plugin.

        'plugin' should be a Plugin object and that's why this
        method is internal. There is no public way to get an
        instance of a Plugin class
        """
        plugin.deactivate()
        self._activated_plugins.remove(plugin)

    def deactivate_plugin(self, plugin_name):
        """
        Deactivate the plugin with that name
        """
        for p in self._activated_plugins:
            if p.name == plugin_name:
                self._deactivate_plugin_internal(p)
                return

    def show_plugin_preferences(self, plugin_name, parent_window):
        if plugin_name not in list(self._plugins.keys()):
            raise PluginInfoError("There is no plugin with the name %s" %
                                  plugin_name)

        for p in self._activated_plugins:
            if p.name == plugin_name:
                dialog = p.get_configuration_dialog(parent_window)
                if dialog:
                    dialog.run()
                    dialog.destroy()
                return

        raise PluginInfoError("There is no activated plugin with the name %s" %
                              plugin_name)
