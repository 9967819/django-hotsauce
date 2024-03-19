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

import gtk

from kiwi.component import get_utility
from kiwi.environ import environ

from gazpacho.config import config
from gazpacho.interfaces import IGazpachoApp, IPluginManager
from gazpacho.loader.loader import ObjectBuilder

(COL_ACTIVATED,
 COL_TITLE,
 COL_PLUGININFO) = list(range(3))

class PreferencesDialog:
    def __init__(self):
        self.app = get_utility(IGazpachoApp)
        self.plugin_manager = get_utility(IPluginManager)
        ui_file = environ.find_resource('glade', 'preferences.glade')
        app_window = self.app.get_window()

        self.ob = ObjectBuilder(ui_file)
        self.dialog = self.ob.get_widget('dialog')

        # dialog setup
        self.dialog.set_modal(True)
        self.dialog.set_transient_for(app_window)

        # this should go into the glade file as soon as we get support for it
        close = self.ob.get_widget('close')
        close.connect('clicked', self.on_close__clicked)

        # setup each tab
        self._setup_plugins_tab()

    def on_close__clicked(self, button):
        self.dialog.response(gtk.RESPONSE_CLOSE)

    def run(self):
        self.dialog.show()
        self.dialog.run()
        self.dialog.destroy()

    def _setup_plugins_tab(self):
        plugin_list = self.ob.get_widget('plugins_list')

        model = gtk.ListStore(bool, str, object)

        # fill the model
        for plugin_info in self.plugin_manager.get_plugins():
            activated = self.plugin_manager.is_activated(plugin_info.name)
            model.append((activated, plugin_info.title, plugin_info))

        plugin_list.set_model(model)

        # make the cells editable
        toggle = self.ob.get_widget('treeviewcolumn1-renderer1')
        toggle.set_property('activatable', True)
        toggle.connect('toggled', self.on_plugin__activated, model)

        # disable buttons
        plugin_about = self.ob.get_widget('plugin_about')
        plugin_about.set_sensitive(False)
        plugin_about.connect('clicked', self.on_plugin_about__clicked)

        plugin_preferences = self.ob.get_widget('plugin_preferences')
        plugin_preferences.set_sensitive(False)
        plugin_preferences.connect('clicked', self.on_plugin_prefs__clicked)

        selection = plugin_list.get_selection()
        selection.connect('changed', self.on_plugin_selection__changed)

    def on_plugin__activated(self, cell, path, model):
        row = model[path]
        new_value = not row[COL_ACTIVATED]
        row[COL_ACTIVATED] = new_value

        plugin = row[COL_PLUGININFO]

        if new_value:
            self.plugin_manager.activate_plugin(plugin.name, self.app)
        else:
            self.plugin_manager.deactivate_plugin(plugin.name)

        plugin_preferences = self.ob.get_widget('plugin_preferences')
        plugin_preferences.set_sensitive(new_value)

        config.set_plugin(plugin.name, new_value)

    def on_plugin_selection__changed(self, selection):
        model, model_iter = selection.get_selected()
        plugin_about = self.ob.get_widget('plugin_about')
        plugin_preferences = self.ob.get_widget('plugin_preferences')
        if model_iter:
            plugin_about.set_sensitive(True)
            activated = model.get_value(model_iter, COL_ACTIVATED)
            plugin_preferences.set_sensitive(activated)

        else:
            plugin_about.set_sensitive(False)
            plugin_preferences.set_sensitive(False)

    def on_plugin_about__clicked(self, button):
        plugin_info = self._get_selected_plugin()
        if plugin_info:
            dialog = gtk.AboutDialog()
            dialog.set_name(plugin_info.title)
            dialog.set_version(plugin_info.version)
            dialog.set_comments(plugin_info.description)
            dialog.set_authors([plugin_info.author])
            dialog.set_transient_for(self.dialog)
            dialog.run()
            dialog.destroy()

    def on_plugin_prefs__clicked(self, button):
        plugin_info = self._get_selected_plugin()
        if plugin_info:
            self.plugin_manager.show_plugin_preferences(plugin_info.name,
                                                        self.dialog)

    def _get_selected_plugin(self):
        plugin_list = self.ob.get_widget('plugins_list')
        selection = plugin_list.get_selection()
        model, model_iter = selection.get_selected()
        if model_iter:
            return model.get_value(model_iter, COL_PLUGININFO)
