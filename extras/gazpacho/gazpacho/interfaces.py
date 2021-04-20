# Copyright (C) 2005 by Async Open Source
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

from kiwi.component import Attribute, Interface

class BaseWidgetAdaptor:
    name = None
    type = None

class BaseLibrary:
    def __init__(self, name, library_name):
        pass

    def create_widget(self, gtype):
        pass

class IGazpachoApp(Interface):
    """Provides a gazpacho application"""

    add_class = Attribute('add_class')

    def get_current_project(self):
        pass

    def get_window(self):
        pass


class IReferencable(Interface):
    """This interface provides means for clearing and restoring
    references to a gadget.

    Every deletable object that will keep a reference to a gadget
    should implement this interface. The object implementing this
    interface will also be responsible for adding and removing itself
    to the reference container for the gadget to which it refers.
    """

    def remove_reference(gadget):
        """
        This method will be called by the reference manager when the
        gadget has been removed or deleted.
        """
        pass

    def add_reference(gadget):
        """
        This method will be called by the reference manager when a
        deleted gadget has been restored.
        """
        pass


class IPluginManager(Interface):
    """Manages a set of plugins

    Takes care of loading the plugins and activating/deactivating
    them.

    It search for plugins in $datadir/plugins and also in the user home
    directory (~/.gazpacho/plugins). The later location takes preference
    over the system wide plugin directory.

    Every plugin should be a python package with a .desktop file containing
    some metadata. Check the PluginInfo class for information about that
    metadata
    """

    def load_plugins():
        """Load plugins in the standard plugins directories"""

    def load_plugins_dir(dirname):
        """Load plugins in the specified directory"""

    def get_plugins():
        """Returns a list of PluginInfo objects that represents the
        loaded plugins"""

    def is_activated(plugin_name):
        """True if a plugin with that name is activated"""

    def activate_plugins(plugin_names):
        """Activate all the plugins in the list plugin_names"""

    def activate_plugin(plugin_name):
        """Activate just the plugin with the name 'plugin_name'"""

    def deactivate_all():
        """Deactivate all plugins that are activated"""

    def deactivate_plugin(plugin):
        """Deactivate just the plugin passed as the argument.

        The argument can be a plugin name or a Plugin instance
        """
