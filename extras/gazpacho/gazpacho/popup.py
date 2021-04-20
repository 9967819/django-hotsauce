# Copyright (C) 2004,2005 by SICEm S.L. and Imendio AB
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

from gazpacho import gapi, util
from gazpacho.clipboard import clipboard
from gazpacho.command import ContainerCommand
from gazpacho.commandmanager import command_manager
from gazpacho.properties import CommandSetProperty
from gazpacho.i18n import _

class Popup(object):
    """This class defines a popup menu and its behaviour

    This popup menu has entries for selecting the widget, cut/copy/paste it
    and deleting it.

    It also shows a submenu for every parent widget in the hierarchy.
    """
    def __init__(self, command_manager, gadget):
        self._command_manager = command_manager
        self._gadget = gadget
        self._popup_menu = self._create_menu(gadget)

    def pop(self, event):
        """Call this method if you want the menu to show up"""
        if event:
            button = event.button
            event_time = event.time
        else:
            button = 0
            event_time = 0

        self._popup_menu.popup(None, None, None, button, event_time)
        return self._popup_menu

    # callbacks for the actions
    def _select_cb(self, item, gadget):
        if gadget:
            gadget.select()

    def _cut_cb(self, item, gadget):
        clipboard.cut(gadget)

    def _copy_cb(self, item, gadget):
        clipboard.copy(gadget)

    def _paste_cb(self, item, placeholder):
        gadget = util.get_parent(placeholder)
        if isinstance(placeholder, gtk.TreeView):
            from gazpacho.gadget import Gadget
            clipboard.paste(Gadget.from_widget(placeholder))
        else:
            clipboard.paste(placeholder, gadget.project)

    def _delete_cb(self, item, gadget):
        gapi.delete_gadget(gadget.project, gadget)

    def _box_insert_cb(self, item, gadget, after):
        from gazpacho.widgets.base.box import CommandBoxInsertPlaceholder
        parent_pos = self._find_parent_box_and_pos(gadget)
        if parent_pos is None:
            return

        (parent, pos) = parent_pos
        cmd = CommandBoxInsertPlaceholder(parent, pos, after)
        self._command_manager.execute(cmd, parent.project)

    def _table_insert(self, gadget, row=False, column=False, before=False):
        from gazpacho.gadget import Gadget

        selected = gadget.project.selection[0]
        table = gadget.widget

        # First resize table
        if row:
            old_prop_name = 'top-attach'
            n_rows = gadget.get_prop('n-rows')
            cmds = [CommandSetProperty(n_rows, n_rows.value + 1)]
            desc = 'row'
        elif column:
            old_prop_name = 'left-attach'
            n_columns = gadget.get_prop('n-columns')
            cmds = [CommandSetProperty(n_columns, n_columns.value + 1)]
            desc = 'column'
        else:
            raise AssertionError

        # XXX: Remove this hack, it is selection related, the table
        #      might be selected when we enter here. Requires UI changes
        try:
            old = table.child_get_property(selected, old_prop_name)
        except TypeError:
            return

        if before:
            old -= 1

        # Secondly move children
        for child in table.get_children():
            child_gadget = Gadget.from_widget(child)
            # No need to move placeholders
            if not child_gadget:
                continue

            if row:
                pos = child_gadget.get_child_prop('y-pos')
            else: # column
                pos = child_gadget.get_child_prop('x-pos')

            if pos.value > old:
                cmds.append(CommandSetProperty(pos, pos.value + 1))

        # Execute everything in one go
        command_manager.execute(
            ContainerCommand('Adding a %s to table' % desc, *cmds),
            gadget.project)

    def _table_insert_row_before_cb(self, item, gadget):
        self._table_insert(gadget, row=True, before=True)

    def _table_insert_row_after_cb(self, item, gadget):
        self._table_insert(gadget, row=True)

    def _table_insert_column_before_cb(self, item, gadget):
        self._table_insert(gadget, column=True, before=True)

    def _table_insert_column_after_cb(self, item, gadget):
        self._table_insert(gadget, column=True)

    # aux methods
    def _create_menu(self, gadget, add_children=True):
        from gazpacho.placeholder import Placeholder
        popup_menu = gtk.Menu()

        self._append_item(popup_menu, None,
                          _('Select')+' '+gadget.name,
                          True,
                          self._select_cb, gadget)
        self._append_item(popup_menu, gtk.STOCK_CUT, None, True,
                          self._cut_cb, gadget)
        self._append_item(popup_menu, gtk.STOCK_COPY, None, True,
                          self._copy_cb, gadget)
        if isinstance(gadget, Placeholder):
            self._append_item(popup_menu, gtk.STOCK_PASTE, None, True,
                              self._paste_cb, gadget)
        self._append_item(popup_menu, gtk.STOCK_DELETE, None, True,
                          self._delete_cb, gadget)

        if isinstance(gadget.widget, gtk.Box):
            separator = gtk.MenuItem()
            separator.show()
            popup_menu.append(separator)

            self._append_item(popup_menu, _('Insert before'), None, True,
                              self._box_insert_cb, gadget, False)

            self._append_item(popup_menu, _('Insert after'), None, True,
                              self._box_insert_cb, gadget, True)
        elif isinstance(gadget.widget, gtk.Table):
            self._append_item(popup_menu, _('Insert row before'), None, True,
                              self._table_insert_row_before_cb, gadget)
            self._append_item(popup_menu, _('Insert row after '), None, True,
                              self._table_insert_row_after_cb, gadget)
            self._append_item(popup_menu, _('Insert column before'), None, True,
                              self._table_insert_column_before_cb, gadget)
            self._append_item(popup_menu, _('Insert column after '), None, True,
                              self._table_insert_column_after_cb, gadget)

        if add_children and not gadget.is_toplevel():
            parent = gadget.get_parent()
            self._populate_children(popup_menu, parent)

        return popup_menu

    def _append_item(self, menu, stock, label, sensitive, callback, *data):
        if stock:
            menu_item = gtk.ImageMenuItem(stock, None)
        else:
            menu_item = gtk.MenuItem(label, False)

        menu_item.connect('activate', callback, *data)

        menu_item.set_sensitive(sensitive)
        menu_item.show()
        menu.append(menu_item)

    def _populate_children(self, popup_menu, parent):
        while parent:
            separator = gtk.MenuItem()
            separator.show()
            popup_menu.append(separator)

            child = gtk.MenuItem(parent.name, False)
            child_menu = self._create_child_menu(parent)
            child.set_submenu(child_menu)
            child.show()
            popup_menu.append(child)

            parent = parent.get_parent()

    def _create_child_menu(self, parent):
        return Popup._create_menu(self, parent, False)

    # Used for finding the parent box to insert placeholder in
    def _find_parent_box_and_pos(self, gadget):
        from gazpacho import placeholder
        if isinstance(self._gadget, placeholder.Placeholder):
            child_widget = self._gadget
            parent = util.get_parent(self._gadget)
        else:
            child_widget = self._gadget.widget
            parent = self._gadget.get_parent()

        while parent:
            if parent == gadget:
                break

            child_widget = parent.widget
            parent = parent.get_parent()

        if parent is not None and child_widget is not None:
            pos = parent.widget.get_children().index(child_widget)

            return parent, pos


class PlaceholderPopup(Popup):
    def _delete_placeholder_cb(self, item, placeholder):
        from gazpacho.widgets.base.box import CommandBoxDeletePlaceholder

        parent = util.get_parent(placeholder)
        if len(parent.widget.get_children()) >= 1:
            cmd = CommandBoxDeletePlaceholder(placeholder)
            self._command_manager.execute(cmd, parent.project)

    def _create_menu(self, placeholder, add_children=False):
        from gazpacho.clipboard import clipboard
        popup_menu = gtk.Menu()

        # Paste menu item
        item = clipboard.get_selected_item()
        enable_paste = False
        if item and not item.is_toplevel:
            enable_paste = True
        self._append_item(popup_menu, gtk.STOCK_PASTE, None, enable_paste,
                          self._paste_cb, placeholder)

        # Delete menu item
        self._append_item(popup_menu, gtk.STOCK_DELETE, None,
                          placeholder.is_deletable(),
                          self._delete_placeholder_cb, placeholder)

        parent = util.get_parent(placeholder)
        self._populate_children(popup_menu, parent)

        return popup_menu

