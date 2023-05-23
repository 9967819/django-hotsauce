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

import gtk

from kiwi.environ import environ

# XXX: Move to a file
MAIN_UI_STRING = """
<ui>
  <menubar name="MainMenu">
    <menu action="FileMenu">
      <menuitem action="New"/>
      <menuitem action="Open"/>
      <separator name="FM1"/>
      <menuitem action="Save"/>
      <menuitem action="SaveAs"/>
      <separator name="FM2"/>
      <placeholder name="RecentProjects"/>
      <separator name="FM3"/>
      <menuitem action="Close"/>
      <menuitem action="Quit"/>
    </menu>
    <menu action="EditMenu">
      <menuitem action="Undo"/>
      <menuitem action="Redo"/>
      <separator name="EM1"/>
      <menuitem action="Cut"/>
      <menuitem action="Copy"/>
      <menuitem action="Paste"/>
      <menuitem action="Delete"/>
      <separator name="EM2"/>
      <menuitem action="ShowStructure"/>
      <menuitem action="ShowWorkspace"/>
      <separator name="EM3"/>
      <menuitem action="Preferences"/>
    </menu>
    <menu action="ObjectMenu">
    </menu>
    <menu action="ProjectMenu">
      <placeholder name="OpenProjects"/>
      <separator name="project-separtor"/>
      <menuitem action="ProjectProperties"/>
    </menu>
    <menu action="DebugMenu">
      <menuitem action="ShowCommandStack"/>
      <menuitem action="ShowClipboard"/>
      <separator/>
      <menuitem action="Preview"/>
      <menuitem action="DumpData"/>
    </menu>
    <menu action="HelpMenu">
      <menuitem action="About"/>
    </menu>
  </menubar>
  <toolbar name="MainToolbar">
    <toolitem action="Open"/>
    <toolitem action="Save"/>
    <separator name="MT1"/>
    <toolitem action="Undo"/>
    <toolitem action="Redo"/>
    <separator name="MT2"/>
    <toolitem action="Cut"/>
    <toolitem action="Copy"/>
    <toolitem action="Paste"/>
    <separator name="MT3"/>
  </toolbar>
</ui>
"""

class BarManager(object):
    """
    Can I have a beer with that please?
    """

    def __init__(self):
        # Mapping of action group name -> ActionGroup
        self._action_groups = {}
        # Mapping of action name -> Action
        self._action_cache = {}

        self._ui_manager = gtk.UIManager()

        # Create action groups
        for group_name in ['Normal', 'ContextActions',
                           'OpenProjects',
                           'RecentProjects']:
            self._create_action_group(group_name)
        self._create_action_group('AlwaysDisabled', False)

    def build_interfaces(self):
        self._ui_manager.add_ui_from_string(MAIN_UI_STRING)

        # Make sure that the project and object menu isn't removed if empty
        self.set_action_prop('ProjectMenu', hide_if_empty=False)
        self.set_action_prop('ObjectMenu', hide_if_empty=False)

        toolbar = self.get_toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)

        # Disable workspace for older versions of PyGTK.
        if gtk.pygtk_version < (2, 8):
            self.set_action_prop('ShowWorkspace', sensitive=False)

    def _create_action_group(self, name, sensitive=True):
        action_group = gtk.ActionGroup(name)
        action_group.set_sensitive(sensitive)
        self.add_action_group(action_group)
        return action_group

    def add_action_group(self, action_group):
        self._action_groups[action_group.get_name()] = action_group
        self._ui_manager.insert_action_group(action_group, 0)
        for action in action_group.list_actions():
            self._action_cache[action.get_name()] = action

    def remove_action_group(self, name):
        action_group = self._action_groups[name]
        del self._action_groups[name]
        self._ui_manager.remove_action_group(action_group)
        for action in action_group.list_actions():
            del self._action_cache[action.get_name()]

    def get_group(self, group_name):
        """
        @param group_name: name of an action group
        """
        if not group_name in self._action_groups:
            raise ValueError("There is no action group called %s" % group_name)
        return self._action_groups[group_name]

    def has_group(self, group_name):
        """
        @param group_name: name of an action group
        """
        return group_name in self._action_groups

    def add_action(self, group_name, action):
        """
        @param group_name: name of an action group
        @param action: a gtk.Action
        """
        if not isinstance(action, gtk.Action):
            raise TypeError("action must be a gtk.Action")

        action_group = self.get_group(group_name)

        action_name = action.get_name()
        if action_name in self._action_cache:
            action_group.remove_action(action)

        action_group.add_action(action)
        self._action_cache[action_name] = action

    def add_actions(self, group_name, *actions):
        """
        @param group_name: name of an action group
        @param actions: sequence of action tuples
        """
        action_group = self.get_group(group_name)
        action_group.add_actions(actions)
        for action in actions:
            name = action[0]
            action = action_group.get_action(name)
            self._action_cache[name] = action

    def add_toggle_actions(self, group_name, *actions):
        """
        @param group_name: name of an action group
        @param actions: sequence of toggle action tuples
        """
        action_group = self.get_group(group_name)
        action_group.add_toggle_actions(actions)
        for action in actions:
            name = action[0]
            action = action_group.get_action(name)
            self._action_cache[name] = action

    def set_action_prop(self, action_name, **properties):
        """
        Gets an action and sets properties of it.
        Note that action needs to be added through add_action,
        add_actions or add_toggle_actions in this class.
        @param action_name: name of an action
        @param properties: properties to set
        """
        action = self._get_action(action_name)
        for key, value in list(properties.items()):
            action.set_property(key, value)

    def set_action_props(self, action_names, **properties):
        """
        An extended version of set_action_props, which takes a sequence
        of action_names instead of just a name of one action
        @param action_names: a sequence of names of actions
        @param properties: properties to set
        """
        if not isinstance(action_names, (list, tuple)):
            raise TypeError("action_names must be a list or tuple")

        for action_name in action_names:
            self.set_action_prop(action_name, **properties)

    def activate_action(self, name):
        """
        Activate the specified action.

        @param name: the action name
        @type name: str
        """
        action = self._get_action(name)
        action.activate()

    def _get_action(self, action_name):
        """
        Get the first occurence of an action with the given name.

        @param action_name: the name of the action
        @type action_name: str

        @return: the action
        @rtype: gtk.Action
        """
        if not action_name in self._action_cache:
            raise ValueError("No action called: %s" % action_name)

        return self._action_cache[action_name]


    # GtkUIManager delegators

    def get_menubar(self):
        return self._ui_manager.get_widget('/MainMenu')

    def get_toolbar(self):
        return self._ui_manager.get_widget('/MainToolbar')

    def get_accel_group(self):
        return self._ui_manager.get_accel_group()

    def get_action(self, action_name):
        return self._ui_manager.get_action(action_name)

    def get_widget(self, widget_name):
        return self._ui_manager.get_widget(widget_name)

    def remove_ui(self, uid):
        self._ui_manager.remove_ui(uid)

    def add_ui_from_string(self, ui_string):
        return self._ui_manager.add_ui_from_string(ui_string)

    def ensure_update(self):
        self._ui_manager.ensure_update()

if environ.epydoc:
    bar_manager = object()
else:
    bar_manager = BarManager()
