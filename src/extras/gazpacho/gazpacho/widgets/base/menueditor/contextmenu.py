"""Context menus with options to edit menus"""
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

from gazpacho.actioneditor import CommandAddRemoveAction, CommandEditAction
from gazpacho.commandmanager import command_manager
from gazpacho.i18n import _
from gazpacho.stockicons import StockIconDialog

class ContextMenu(gtk.Menu):
    """Base class for context menus for MenuBar and Menu widgets"""

    def __init__(self, context):
        """Constructor.

        Context must be the MenuItem instance where the  user clicked
        with the right button
        """
        gtk.Menu.__init__(self)

        self.context = context

        self._create_options()
        self.show_all()

    def _create_options(self):
        """Create the menu items. Subclasses should override this method"""

    def _on_edit__activate(self, item):
        """Edit item callback"""
        self.context.start_editing()

    def _on_previous__activate(self, item):
        """Previous item callback

        Moves the context one position before where it was.
        """
        parent = self.context.parent
        i = parent.children.index(self.context)
        parent.remove(self.context)
        parent.insert(self.context, i - 1)

        menu_bar = self.context.get_menu_bar()
        menu_bar.update_ui()

    def _on_next__activate(self, item):
        """Next item callback.

        Moves the context one position after where it was.
        """
        parent = self.context.parent
        i = parent.children.index(self.context)
        parent.remove(self.context)
        parent.insert(self.context, i + 1)

        menu_bar = self.context.get_menu_bar()
        menu_bar.update_ui()

    def _on_delete__activate(self, item):
        """Delete item callback.

        Removes the context from its parent.
        """
        gadget = self.context.gadget
        if gadget:
            action_group = self.context.action_group
            action = self.context.action
            cmd = CommandAddRemoveAction(action_group, action, False)
            project = gadget.project
            command_manager.execute(cmd, project)

        menu_bar = self.context.get_menu_bar()
        self.context.parent.remove(self.context)
        menu_bar.update_ui()

class MenuBarContextMenu(ContextMenu):
    """Context menu for MenuBar widgets"""

    def _create_options(self):
        """Creates edit, left, right and delete items"""
        edit = gtk.ImageMenuItem(gtk.STOCK_EDIT)
        edit.connect('activate', self._on_edit__activate)
        self.append(edit)

        self.append(gtk.SeparatorMenuItem())

        go_somewhere = False

        if not self.context.is_first():
            # The first item can not be moved to the left
            move_left = gtk.ImageMenuItem(gtk.STOCK_GO_BACK)
            move_left.connect('activate', self._on_previous__activate)
            self.append(move_left)
            go_somewhere = True

        if not self.context.is_last():
            # The last item can not be moved to the right
            move_right = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
            move_right.connect('activate', self._on_next__activate)
            self.append(move_right)
            go_somewhere = True

        if go_somewhere:
            self.append(gtk.SeparatorMenuItem())

        delete = gtk.ImageMenuItem(gtk.STOCK_DELETE)
        delete.connect('activate', self._on_delete__activate)
        self.append(delete)

class MenuContextMenu(ContextMenu):
    """Context menu for Menu widgets"""

    def _create_options(self):
        """Creates edit, up, bottom, new group, add/remove submenu, set image,
        set accelerator and delete items"""
        edit = gtk.ImageMenuItem(gtk.STOCK_EDIT)
        edit.connect('activate', self._on_edit__activate)
        self.append(edit)

        self.append(gtk.SeparatorMenuItem())

        go_somewhere = False

        if not self.context.is_first():
            # The first item can not be moved up
            move_up = gtk.ImageMenuItem(gtk.STOCK_GO_UP)
            move_up.connect('activate', self._on_previous__activate)
            self.append(move_up)
            go_somewhere = True

        if not self.context.is_last():
            # The last item can not be moved down
            move_down = gtk.ImageMenuItem(gtk.STOCK_GO_DOWN)
            move_down.connect('activate', self._on_next__activate)
            self.append(move_down)
            go_somewhere = True

        if go_somewhere:
            self.append(gtk.SeparatorMenuItem())

        # A new group has a separator just before it
        new_group = self.context.is_new_group()
        start_new_group = gtk.CheckMenuItem(_('Start new group'))
        start_new_group.set_active(new_group)
        start_new_group.connect('toggled',
                                self._on_start_new_group__toggled)
        self.append(start_new_group)

        if self.context.submenu:
            # let the user remove the submenu
            submenu = gtk.MenuItem(_('Remove submenu'))
            submenu.connect('activate', self._on_remove_submenu__activate)
        else:
            # or add a new one
            submenu = gtk.MenuItem(_('Add submenu'))
            submenu.connect('activate', self._on_add_submenu__activate)

        self.append(submenu)

        self.append(gtk.SeparatorMenuItem())

        # Let the user set a stock image
        image = gtk.MenuItem(_('Set image'))
        image.connect('activate', self._on_image__activate)
        self.append(image)

        # Or an accelerator ( TODO )
        #accel = gtk.MenuItem(_('Set accelerator'))
        #accel.connect('activate', self._on_accel__activate)
        #self.append(accel)

        self.append(gtk.SeparatorMenuItem())

        delete = gtk.ImageMenuItem(gtk.STOCK_DELETE)
        delete.connect('activate', self._on_delete__activate)
        self.append(delete)

    def _on_start_new_group__toggled(self, item):
        """Start new group item callback.

        Add or remove a separator before the context depending on the
        previous existence of the separator
        """
        from . import widgets
        parent = self.context.parent
        i = parent.children.index(self.context)

        if item.get_active() and not self.context.is_new_group():
            # Add a separator before the context
            separator = widgets.SeparatorMenuItem()
            separator.show()
            parent.insert(separator, i)

        elif not item.get_active() and self.context.is_new_group():
            # remove the separator before the context
            separator = parent.children[i - 1]
            parent.remove(separator)

        # create the UI definition
        menu_bar = self.context.get_menu_bar()
        menu_bar.update_ui()

    def _on_add_submenu__activate(self, item):
        """Add submenu item callback.

        Add a submenu on the context
        """
        from . import widgets
        submenu = widgets.Menu(self.context.parent.gadget)
        self.context.set_submenu(submenu)

    def _on_remove_submenu__activate(self, item):
        """Remove submenu item callback

        Removes the submenu of the context
        """
        if self.context.submenu:
            self.context.submenu.popdown()
            self.context.set_submenu(None)

    def _on_image__activate(self, item):
        """Image item callback

        Pop up a dialog with the stock icons so the user can select one of
        those. TODO: let the user reset the image to None
        """
        dialog = StockIconDialog()
        if gtk.RESPONSE_OK == dialog.run():
            stock_id = dialog.get_selected()

            # Update the action
            action = self.context.action
            project = self.context.gadget.project
            values = {
                'name' : action.name,
                'label': action.label,
                'short_label': action.short_label,
                'is_important': action.is_important,
                'stock_id': stock_id,
                'tooltip': action.tooltip,
                'accelerator': action.accelerator,
                'callback': action.callback,
                }
            cmd = CommandEditAction(action, values, project)
            command_manager.execute(cmd, project)

            self.context.set_action(action)

        dialog.destroy()
