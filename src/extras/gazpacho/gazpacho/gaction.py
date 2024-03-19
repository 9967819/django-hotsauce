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

import gtk
import gobject
from kiwi.utils import gsignal, type_register

class GAction(object):
    """A GAction has the same information that a GtkAction but it
    is easier to work with. The menubar/toolbar editor code will
    convert this GActions to GtkActions and viceversa.
    """
    def __init__(self, parent, name='', label='',
                 short_label='', is_important=False,
                 tooltip='', stock_id=None, callback='', accel=''):
        # parent GActionGroup
        self.parent = parent

        self.name = name
        self.label = label
        if short_label:
            self.short_label = short_label
        else:
            self.short_label = label
        self.is_important = is_important
        self.tooltip = tooltip
        self.stock_id = stock_id
        self.callback = callback
        self.accelerator = accel

    #@classmethod
    def new(cls, gtk_action, parent):
        """Create a new GAction from a GtkAction and a GtkActionGroup"""
        # This code is similar to code in the loader, investigate
        # if we can use more code reusage
        name = gtk_action.get_name()
        label = gtk_action.get_property('label')
        short_label = gtk_action.get_property('short-label')
        is_important = gtk_action.get_property('is-important')
        tooltip = gtk_action.get_property('tooltip')
        stock_id = gtk_action.get_property('stock-id') or None
        gaction = cls(parent, name, label, short_label, is_important,
                      tooltip, stock_id)

        # check if it has accelerator
        accel_entry = gtk.accel_map_lookup_entry('<Actions>/%s/%s' %
                                                 (parent.name, name))
        if accel_entry:
            key, modifier = accel_entry
            if key != 0:
                gaction.accelerator = gtk.accelerator_name(key, modifier)

        # check if it has signal handler
        callback = gtk_action.get_data('handler')
        if callback:
            gaction.callback = callback

        return gaction
    new = classmethod(new)

    def __str__(self):
        return "%s %s %s %u %s %s %s" % (
            self.name, self.label, self.short_label, self.is_important,
            self.stock_id, self.accelerator, self.tooltip)

    def get_name(self):
        return self.name

class GActionGroup(gobject.GObject):
    """A GActionGroup is just a list of GActions with a name.
    Associated with each GActionGroup there is a GtkActionGroup with
    is keep synchronized with the GActionGroup:

        - As we can't change the name of a GtkActionGroup, if the
        user change the name of a GActionGroup we have to regenerate
        the GtkActionGroup again, copying the actions from the old one
        to the new one.

        - When an action is added or removed, we create or destroy the
        GtkAction associated with it. If an action is only changed, we
        regenerate the GtkAction and tell the UIManager to update itself
        by removing the GtkActionGroup and then addind it again.
        Anyone knows a better way to do so?
    """
    gsignal('add-action', object)
    gsignal('remove-action', object)

    def __init__(self, name=''):
        gobject.GObject.__init__(self)
        self._name = name
        self._actions = {}
        self._uimanager = None

    #@classmethod
    def new(cls, action_group):
        return cls(action_group.get_name())
    new = classmethod(new)

    def create_gtk_action_group(self, uimanager):
        self._uimanager = uimanager
        gtk_action_group = gtk.ActionGroup(self.name)
        gtk_action_group.set_data('gaction_group', self)
        self.set_data('gtk_action_group', gtk_action_group)
        self._uimanager.insert_action_group(gtk_action_group, 0)
        return gtk_action_group

    def destroy_gtk_action_group(self):
        gtk_action_group = self.get_data('gtk_action_group')
        self.set_data('gtk_action_group', None)
        self._uimanager.remove_action_group(gtk_action_group)

    def get_name(self):
        return self._name

    def set_name(self, new_name):
        """GtkAction groups can't change their name

        That's why we need to copy the old one into a new one
        """
        self._name = new_name

        if self._uimanager is None:
            return

        gtk_action_group = self.get_data('gtk_action_group')
        self._uimanager.remove_action_group(gtk_action_group)
        new_gtk_action_group = self.create_gtk_action_group(self._uimanager)

        for action in gtk_action_group.list_actions():
            gtk_action_group.remove_action(action)
            new_gtk_action_group.add_action(action)

    name = property(get_name, set_name)

    def add_action(self, action):
        self._actions[action.get_name()] = action

        self._add_gtk_action(action)

        self.emit('add-action', action)

    def add_actions(self, actions):
        # now create the default actions
        for (name, label, short, is_important,
             tooltip, stock_id, callback, acc) in actions:
            # check if the action already exists
            if name not in self._actions:
                ga = GAction(self, name, label, short, is_important,
                             tooltip, stock_id, callback, acc)
                self.add_action(ga)
            # XXX maybe we still want to add the action if its contents
            # are not exactly the same as the old one

    def _add_gtk_action(self, action):
        gtk_action = gtk.Action(action.name, action.label,
                                action.tooltip, action.stock_id)
        # don't set a zero-length short label
        if action.short_label:
            gtk_action.set_property('short-label', action.short_label)
        gtk_action.set_property('is-important', action.is_important)
        gtk_action_group = self.get_data('gtk_action_group')
        gtk_action_group.add_action_with_accel(gtk_action, action.accelerator)

    def remove_action(self, action):
        del self._actions[action.get_name()]
        self._remove_gtk_action(action.name)
        self.emit('remove-action', action)

    def _remove_gtk_action(self, name):
        gtk_action_group = self.get_data('gtk_action_group')
        gtk_action = gtk_action_group.get_action(name)
        gtk_action_group.remove_action(gtk_action)

    def update_action(self, action, old_name):
        self._remove_gtk_action(old_name)
        self._add_gtk_action(action)
        del self._actions[old_name]
        self._actions[action.name] = action
        if self._uimanager is not None:
            # we need to remove it and then add it to the uimanager
            # so all the proxies are updated
            gtk_action_group = self.get_data('gtk_action_group')
            self._uimanager.remove_action_group(gtk_action_group)
            self._uimanager.insert_action_group(gtk_action_group, 0)

    def get_action(self, action_name):
        return self._actions.get(action_name)

    def get_actions(self):
        return list(self._actions.values())

    def get_action_names(self):
        return list(self._actions.keys())

type_register(GActionGroup)

