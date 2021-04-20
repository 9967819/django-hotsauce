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
from kiwi.component import get_utility
from kiwi.ui.dialogs import BaseDialog
from kiwi.utils import gsignal

from gazpacho.app.bars import bar_manager
from gazpacho.command import FlipFlopCommandMixin, Command
from gazpacho.commandmanager import command_manager
from gazpacho.gaction import GAction, GActionGroup
from gazpacho.i18n import _
from gazpacho.interfaces import IGazpachoApp
from gazpacho.stockicons import StockIconList
from gazpacho.signalhandlers import SignalHandlerStorage
from gazpacho.util import select_iter

(COL_OBJECT,) = list(range(1))

class GActionsView(gtk.ScrolledWindow):
    """A GActionsView is basically a TreeView where the actions
    and action groups are shown.

    The data it shows is always a two level hierarchy tree, where
    toplevel nodes are GActionGroups and leaves are GActions.
    """
    gsignal('selection-changed', object)

    def __init__(self, app):
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_IN)

        self._handlers = SignalHandlerStorage()
        self._app = app
        self.project = None

        self._model = gtk.TreeStore(object)
        self._treeview = gtk.TreeView(self._model)
        self._treeview.set_headers_visible(False)
        self._treeview.connect('row-activated', self._row_activated_cb)
        self._treeview.connect('button-press-event', self._button_press_cb)
        self._treeview.connect('key-press-event', self._key_press_cb)
        self._treeview.get_selection().connect('changed',
                                               self._selection_changed_cb)

        column = gtk.TreeViewColumn()
        renderer1 = gtk.CellRendererPixbuf()
        column.pack_start(renderer1, expand=False)
        column.set_cell_data_func(renderer1, self._draw_action, 0)

        renderer2 = gtk.CellRendererText()
        column.pack_start(renderer2, expand=True)
        column.set_cell_data_func(renderer2, self._draw_action, 1)

        self._treeview.append_column(column)

        self.add(self._treeview)
        self._treeview.show()

    def set_project(self, project):
        if self.project:
            self._handlers.disconnect_all()

        self.project = project
        self._model.clear()

        if not project:
            return

        self._handlers.connect(project, 'add-action', self._add_action_cb)
        self._handlers.connect(project, 'remove-action',
                               self._remove_action_cb)
        self._handlers.connect(project, 'action-name-changed',
                               self._action_name_changed_cb)

        self._populate_model()

    def add_action(self, gaction):
        """Create an action and add it to the selected action
        group. This method will not create the action directly but
        delegate to the command manager."""
        if isinstance(gaction, GActionGroup):
            # create an action with the selected action group
            # as the parent
            parent = gaction
        else:
            # create a brother action of the selected action
            parent = gaction.parent

        dialog = GActionDialog(
            get_utility(IGazpachoApp).get_window(), parent, None)
        if dialog.run() == gtk.RESPONSE_OK:
            values = dialog.get_values()
            new_gact = GAction(parent, values['name'], values['label'],
                               values['short_label'], values['is_important'],
                               values['tooltip'], values['stock_id'],
                               values['callback'], values['accelerator'])
            cmd = CommandAddRemoveAction(parent, new_gact, True)
            command_manager.execute(cmd, self.project)

        dialog.destroy()

    def add_action_group(self):
        """Create and add an action group. This method will not create
        the action group directly but delegate to the command manager."""
        # nothing is selected, we create an action group
        dialog = GActionGroupDialog(
            get_utility(IGazpachoApp).get_window(), None)
        if dialog.run() == gtk.RESPONSE_OK:
            name = dialog.get_action_group_name()
            gaction_group = GActionGroup(name)
            cmd = CommandAddRemoveActionGroup(gaction_group, self.project, True)
            command_manager.execute(cmd, self.project)
        dialog.destroy()

    def remove_action(self, gaction):
        """Remove the action group. This method will not remove the
        action group directly but delegate to the command manager."""
        if isinstance(gaction, GActionGroup):
            cmd = CommandAddRemoveActionGroup(gaction, self.project, False)
        else:
            cmd = CommandAddRemoveAction(gaction.parent, gaction, False)

        command_manager.execute(cmd, self.project)

    def edit_action(self, gaction):
        """Edit the action or action group. This method will not edit
        it directly but delegate to the command manager."""
        if isinstance(gaction, GAction):
            dialog = GActionDialog(
                get_utility(IGazpachoApp).get_window(),
                gaction.parent, gaction)
            if dialog.run() == gtk.RESPONSE_OK:
                new_values = dialog.get_values()
                cmd = CommandEditAction(gaction, new_values, self.project)
                command_manager.execute(cmd, self.project)

            dialog.destroy()
        else:
            dialog = GActionGroupDialog(get_utility(IGazpachoApp).get_window(),
                                        gaction)
            if dialog.run() == gtk.RESPONSE_OK:
                new_name = dialog.get_action_group_name()
                cmd = CommandEditActionGroup(gaction, new_name, self.project)
                command_manager.execute(cmd, self.project)

            dialog.destroy()

    def _populate_model(self):
        for gaction_group in self.project.uim.get_action_groups():
            parent_iter = self._model.append(None, (gaction_group,))
            for gaction in gaction_group.get_actions():
                self._model.append(parent_iter, (gaction,))

    def _selection_changed_cb(self, selection, data=None):
        """Callback for selection changes in the tree view."""
        model, it = selection.get_selected()
        item = None
        if it:
            item = model[it][COL_OBJECT]
        self.emit('selection-changed', item)

    def _add_action_cb(self, project, action):
        new_iter = None
        if isinstance(action, GActionGroup):
            new_iter = self._model.append(None, (action,))
        elif isinstance(action, GAction):
            parent = action.parent
            ag_iter = self._find_action_group(parent)
            if ag_iter is not None:
                new_iter = self._model.append(ag_iter, (action,))

        if new_iter:
            select_iter(self._treeview, new_iter)

    def _find_action_group(self, action_group):
        model = self._model
        for row in model:
            if row[COL_OBJECT] == action_group:
                return row.iter

    def _find_action(self, parent_iter, gaction):
        model = self._model
        for row in model[parent_iter].iterchildren():
            if row[COL_OBJECT] == gaction:
                return row.iter

    def _remove_action_cb(self, project, gaction):
        if isinstance(gaction, GActionGroup):
            action_group_iter = self._find_action_group(gaction)
            if action_group_iter is not None:
                del self._model[action_group_iter]
        elif isinstance(gaction, GAction):
            parent_iter = self._find_action_group(gaction.parent)
            if parent_iter is not None:
                child_iter = self._find_action(parent_iter, gaction)
                if child_iter is not None:
                    del self._model[child_iter]

    def _action_name_changed_cb(self, project, gaction):
        action_iter = None
        if isinstance(gaction, GAction):
            parent_iter = self._find_action_group(gaction.parent)
            action_iter = self._find_action(parent_iter, gaction)
        elif isinstance(gaction, GActionGroup):
            action_iter = self._find_action_group(gaction)

        if action_iter is not None:
            path = self._model[action_iter].path
            self._model.row_changed(path, action_iter)

    def get_selected_action(self):
        selection = self._treeview.get_selection()
        model, model_iter = selection.get_selected()
        if model_iter:
            return model[model_iter][COL_OBJECT]

    def get_selected_action_group(self):
        selection = self._treeview.get_selection()
        model, model_iter = selection.get_selected()
        if model_iter:
            gaction = model[model_iter][COL_OBJECT]
            if isinstance(gaction, GActionGroup):
                return gaction

    def _draw_action(self, column, cell, model, iter, model_column):
        action = model[iter][COL_OBJECT]
        if model_column == 0:
            prop = 'stock-id'
            if isinstance(action, GActionGroup):
                data = 'gtk-execute'
            else:
                data = action.stock_id or ''
        elif model_column == 1:
            prop = 'text'
            data = action.name

        cell.set_property(prop, data)

    def _row_activated_cb(self, treeview, path, column):
        gaction = self._model[path][COL_OBJECT]
        self.edit_action(gaction)

    # Keybord interaction callback
    def _key_press_cb(self, view, event):
        """Callback for handling key press events. Right now it's only
        used for deleting actions and action groups."""
        if event.keyval in [gtk.keysyms.Delete, gtk.keysyms.KP_Delete]:
            bar_manager.activate_action('Delete')

    def _button_press_cb(self, view, event):
        """Callback for handling mouse clicks. It is used to show a
        context menu."""
        if event.button != 3:
            return False

        # No need for a context menu if there is no project
        if not self.project:
            return False

        result = view.get_path_at_pos(int(event.x), int(event.y))
        path = None
        if result:
            path = result[0]
            view.set_cursor(path)
            view.grab_focus()

        popup = bar_manager.get_widget('/ActionPopup')
        popup.popup(None, None, None, event.button, event.time)
        return True

gobject.type_register(GActionsView)

class GActionDialog(BaseDialog):
    """This Dialog allows the creation and edition of a GAction."""
    def __init__(self, toplevel, action_group, edit_action=None):
        BaseDialog.__init__(self, parent=toplevel)

        # If we are currently editing the accelerator
        self._accel_editing = False

        # All actions that belong to the action group, except the
        # action we're editing
        self._available_actions = {}
        for action in action_group.get_actions():
            if action == edit_action:
                continue
            self._available_actions[action.name] = action

        if edit_action:
            title = _('Edit Action')
            icon = gtk.STOCK_OK
        else:
            title = _('Add Action')
            icon = gtk.STOCK_ADD
        self.set_title(title)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self._ok_button = self.add_button(icon, gtk.RESPONSE_OK)

        self.set_border_width(6)
        self.set_resizable(False)
        self.set_has_separator(False)
        self.vbox.set_spacing(6)

        self._create_widgets()

        self.action = edit_action

        self.set_default_response(gtk.RESPONSE_OK)

        # Set mnemonic callback for the labels in the buttons.
        for widget in self.action_area.get_children():
            hbox = widget.child.child
            label = hbox.get_children()[1]
            keyval = label.get_property('mnemonic-keyval')
            label.connect('mnemonic-activate',
                          self._on_mnemonic_activate, keyval)

        self.vbox.show_all()

    def _create_widgets(self):

        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        # id
        hbox = gtk.HBox(spacing=6)
        label = self._create_label('_Id', size_group, hbox)
        self.id = gtk.Entry()
        self.id.set_activates_default(True)
        self.id.connect('changed', self._on_id_entry_changed)

        label.set_mnemonic_widget(self.id)
        hbox.pack_start(self.id)
        self.vbox.pack_start(hbox)

        # label
        hbox = gtk.HBox(spacing=6)
        label = self._create_label(_('_Label'), size_group, hbox)
        self.label = gtk.Entry()
        self.label.set_activates_default(True)
        label.set_mnemonic_widget(self.label)
        hbox.pack_start(self.label)
        self.vbox.pack_start(hbox)

        # short label
        hbox = gtk.HBox(spacing=6)
        label = self._create_label(_('S_hort Label'), size_group, hbox)
        self.short_label = gtk.Entry()
        self.short_label.set_activates_default(True)
        label.set_mnemonic_widget(self.short_label)
        hbox.pack_start(self.short_label)
        self.vbox.pack_start(hbox)

        # stock
        hbox = gtk.HBox(spacing=6)
        label = self._create_label(_('_Stock'), size_group, hbox)
        self.stock_enabled = gtk.CheckButton()
        self.stock_enabled.connect('toggled', self._on_stock_check_toggled)
        label.set_mnemonic_widget(self.stock_enabled)
        hbox.pack_start(self.stock_enabled, False, False)
        self.stock = StockIconList()
        self.stock.connect('changed', self._on_stock_changed)
        hbox.pack_start(self.stock)

        self.vbox.pack_start(hbox)

        # is_important
        hbox = gtk.HBox(spacing=6)
        label = self._create_label(_('I_mportant'), size_group, hbox)
        self.is_important = gtk.CheckButton()
        label.set_mnemonic_widget(self.is_important)
        hbox.pack_start(self.is_important, False, False)
        self.vbox.pack_start(hbox)

        # accelerator
        hbox = gtk.HBox(spacing=6)
        label = self._create_label(_('Accele_rator'), size_group, hbox)
        self.accelerator = gtk.Entry()
        self.accelerator.set_activates_default(True)
        self.accelerator.set_text('Press a key combination')
        self.accelerator.connect('key-press-event',
                                        self._on_accelerator_entry_key_press)
        self.accelerator.connect('button-press-event',
                                 self._on_accelerator_entry_button_press)
        self.accelerator.connect('focus-in-event',
                                 self.on_accelerator_focus_in)
        self.accelerator.connect('focus-out-event',
                                 self.on_accelerator_focus_out)
        label.set_mnemonic_widget(self.accelerator)
        hbox.pack_start(self.accelerator)

        self.vbox.pack_start(hbox)

        # tooltip
        hbox = gtk.HBox(spacing=6)
        label = self._create_label(_('_Tooltip'), size_group, hbox)
        self.tooltip = gtk.Entry()
        self.tooltip.set_activates_default(True)
        label.set_mnemonic_widget(self.tooltip)
        hbox.pack_start(self.tooltip)
        self.vbox.pack_start(hbox)

        # callback
        hbox = gtk.HBox(spacing=6)
        label = self._create_label(_('Call_back'), size_group, hbox)
        self.callback = gtk.Entry()
        self.callback.set_activates_default(True)
        label.set_mnemonic_widget(self.callback)
        hbox.pack_start(self.callback)
        self.vbox.pack_start(hbox)

    def _create_label(self, text, size_group, hbox):
        label = gtk.Label()
        label.set_markup_with_mnemonic(text+':')
        label.set_alignment(0.0, 0.5)

        keyval = label.get_property('mnemonic-keyval')
        label.connect('mnemonic-activate', self._on_mnemonic_activate, keyval)

        size_group.add_widget(label)
        hbox.pack_start(label, False, False)
        return label

    def on_accelerator_focus_in(self, widget, event):
        """
        Callback for when the accelerator entry gets focus.
        """
        self._accel_editing = True

    def on_accelerator_focus_out(self, widget, event):
        """
        Callback for when the accelerator entry looses focus.
        """
        self._accel_editing = False

    def _on_mnemonic_activate(self, widget, group_cycling, keyval):
        """
        Callback for the mnemonic activate signal. If we're currently
        editing the accelerator we have to disable the usual mnemonic
        action and use the keyval for as an accelerator value.
        """
        if self._accel_editing:
            key = gtk.accelerator_name(keyval, self.mnemonic_modifier)
            self.accelerator.set_text(key)
            return True

        return False

    def _on_accelerator_entry_key_press(self, entry, event):
        """Callback for handling key events in the accelerator
        entry. Accelerators are added by pressing Ctrl, Shift and/or
        Alt in combination with the desired key. Delete and Backspace
        can be used to clear the entry. No other types of editing is
        possible."""

        # Tab must be handled as normal. Otherwise we can't move from
        # the entry.
        if event.keyval == gtk.keysyms.Tab:
            return False

        modifiers = event.get_state() & gtk.accelerator_get_default_mod_mask()
        modifiers = int(modifiers)

        # Check if we should clear the entry
        clear_keys = [gtk.keysyms.Delete,
                      gtk.keysyms.KP_Delete,
                      gtk.keysyms.BackSpace]

        if modifiers == 0:
            if event.keyval in clear_keys:
                entry.set_text('')
            return True

        # Check if the accelerator is valid and add it to the entry
        if gtk.accelerator_valid(event.keyval, modifiers):
            accelerator = gtk.accelerator_name(event.keyval, modifiers)
            entry.set_text(accelerator)

        return True

    def _on_accelerator_entry_button_press(self, entry, event):
        """Callback for handling mouse clicks on the accelerator
        entry. It is used to show a context menu with a clear item."""
        if event.button != 3:
            return False

        clear_item = gtk.MenuItem(_('_Clear'), True)
        if entry.get_text():
            clear_item.connect_object('activate',
                                      lambda entry: entry.set_text(''),
                                      entry)
        else:
            clear_item.set_property('sensitive', False)

        menu = gtk.Menu()
        menu.append(clear_item)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)
        return True

    def _on_id_entry_changed(self, entry):
        """
        Callback used for disabling the ok button if the name of the
        action is already in use for the specified action group.

        @param entry: the id entry
        @type entry: gtk.Entry
        """
        name = entry.get_text()
        self._ok_button.set_sensitive(name not in self._available_actions)

    def _on_stock_changed(self, stock, stock_id):
        self._update_button()

    def _update_button(self):
        stock_id = self.stock.get_stock_id()
        empty = self.stock_enabled.get_active() and not stock_id
        self._ok_button.set_sensitive(not empty)

    def _on_stock_check_toggled(self, button):
        active = button.get_active()
        self.stock.set_sensitive(active)
        self._update_button()

    def _clear_widgets(self):
        self.id.set_text('')
        self.label.set_text('')
        self.short_label.set_text('')
        self.is_important.set_active(False)
        self.stock_enabled.set_active(False)
        self.stock.reset()
        self.accelerator.set_text('')
        self.tooltip.set_text('')
        self.callback.set_text('')

    def _load_widgets(self):
        self.id.set_text(self._action.name)
        self.label.set_text(self._action.label)
        self.short_label.set_text(self._action.short_label or '')
        self.is_important.set_active(self._action.is_important == True)
        if self._action.stock_id is None:
            enabled = False
        else:
            enabled = True
            self.stock.set_stock_id(self._action.stock_id)
        self.stock_enabled.set_active(enabled)

        self.accelerator.set_text(self._action.accelerator or '')
        self.tooltip.set_text(self._action.tooltip or '')
        self.callback.set_text(self._action.callback or '')

    def _fill_action(self):
        self._action.name = self.id.get_text()
        self._action.label = self.label.get_text()
        self._action.short_label = self.short_label.get_text()
        self._action.is_important = self.is_important.get_active()
        if self.stock_enabled.get_active():
            self._action.stock_id = self.stock.get_stock_id()
        else:
            self._action.stock_id = None
        self._action.accelerator = self.accelerator.get_text()
        self._action.tooltip = self.tooltip.get_text()
        self._action.callback = self.callback.get_text()

    def get_action(self):
        self._fill_action()
        return self._action

    def set_action(self, gaction):
        if gaction is None:
            self._clear_widgets()
            self._action = GAction(None)
        else:
            self._action = gaction
            self._load_widgets()

    action = property(get_action, set_action)

    def get_values(self):
        values = dict(name=self.id.get_text(),
                      label=self.label.get_text(),
                      short_label=self.short_label.get_text(),
                      is_important=self.is_important.get_active(),
                      accelerator=self.accelerator.get_text(),
                      tooltip=self.tooltip.get_text(),
                      callback=self.callback.get_text())
        stock_id = None
        if self.stock_enabled.get_active():
            stock_id = self.stock.get_stock_id()
        values['stock_id'] = stock_id

        return values

gobject.type_register(GActionDialog)

class GActionGroupDialog(BaseDialog):
    """This Dialog allows the creation and edition of a GActionGroup."""
    def __init__(self, toplevel=None, action_group=None):
        BaseDialog.__init__(self, parent=toplevel)

        if action_group is None:
            title = _('Add Action Group')
            stock_ok = gtk.STOCK_ADD
        else:
            title = _('Edit Action Group')
            stock_ok = gtk.STOCK_OK
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(stock_ok, gtk.RESPONSE_OK)
        self.set_default_response(gtk.RESPONSE_OK)
        self.set_title(title)
        self.set_border_width(6)
        self.set_resizable(False)
        self.set_has_separator(False)
        self.vbox.set_spacing(6)

        # id
        hbox = gtk.HBox(spacing=6)
        label = gtk.Label()
        label.set_markup_with_mnemonic(_('_Id')+':')
        label.set_alignment(0.0, 0.5)
        hbox.pack_start(label, False, False)
        self._id = gtk.Entry()
        self._id.set_activates_default(True)
        label.set_mnemonic_widget(self._id)
        hbox.pack_start(self._id)
        self.vbox.pack_start(hbox)

        self.action_group = action_group

        self.vbox.show_all()

    def _clear_widgets(self):
        self._id.set_text('')

    def _load_widgets(self):
        self._id.set_text(self._action_group.name)

    def _fill_action_group(self):
        self._action_group.name = self._id.get_text()

    def get_action_group(self):
        self._fill_action_group()
        return self._action_group

    def set_action_group(self, action_group):
        if action_group is None:
            self._clear_widgets()
            self._action_group = GActionGroup(None)
        else:
            self._action_group = action_group
            self._load_widgets()

    action_group = property(get_action_group, set_action_group)

    def get_action_group_name(self):
        return self._id.get_text()

gobject.type_register(GActionGroupDialog)

class CommandAddRemoveAction(FlipFlopCommandMixin, Command):
    def __init__(self, parent, gact, add):
        FlipFlopCommandMixin.__init__(self, add)
        if add:
            description = _('Add action %s') % gact.name
        else:
            description = _('Remove action %s') % gact.name

        Command.__init__(self, description)

        self.gact = gact
        self.parent = parent

    def _add_execute(self):
        self.parent.add_action(self.gact)
    _execute_state1 = _add_execute

    def _remove_execute(self):
        self.parent.remove_action(self.gact)
    _execute_state2 = _remove_execute

class CommandEditAction(Command):
    def __init__(self, gact, new_values, project):
        Command.__init__(self, _('Edit action %s') % gact.name)

        self.new_values = new_values
        self.gact = gact
        self.project = project

    def execute(self):
        old_values = {
            'name' : self.gact.name,
            'label': self.gact.label,
            'short_label': self.gact.short_label,
            'is_important': self.gact.is_important,
            'stock_id': self.gact.stock_id,
            'tooltip': self.gact.tooltip,
            'accelerator': self.gact.accelerator,
            'callback': self.gact.callback,
            }
        self.gact.name = self.new_values['name']
        self.gact.label = self.new_values['label']
        self.gact.short_label = self.new_values['short_label']
        self.gact.is_important = self.new_values['is_important']
        self.gact.stock_id = self.new_values['stock_id']
        self.gact.tooltip = self.new_values['tooltip']
        self.gact.accelerator = self.new_values['accelerator']
        self.gact.callback = self.new_values['callback']
        self.gact.parent.update_action(self.gact, old_values['name'])
        self.new_values = old_values
        self.project.change_action_name(self.gact)

class CommandAddRemoveActionGroup(FlipFlopCommandMixin, Command):
    def __init__(self, gaction_group, project, add):
        FlipFlopCommandMixin.__init__(self, add)
        if add:
            description = _('Add action group %s') % gaction_group.name
        else:
            description = _('Remove action group %s') % gaction_group.name
        Command.__init__(self, description)

        self.project = project
        self.gaction_group = gaction_group
        self.gactions = self.gaction_group.get_actions()

    def _add_execute(self):
        self.project.add_action_group(self.gaction_group)
        for gaction in self.gactions:
            self.gaction_group.add_action(gaction)
        return self.gaction_group
    _execute_state1 = _add_execute

    def _remove_execute(self):
        self.project.remove_action_group(self.gaction_group)
        return self.gaction_group
    _execute_state2 = _remove_execute

class CommandEditActionGroup(Command):
    def __init__(self, gaction_group, new_name, project):
        description = _('Edit action group %s') % gaction_group.name
        Command.__init__(self, description)

        self.new_name = new_name
        self.gaction_group = gaction_group
        self.project = project

    def execute(self):
        old_name = self.gaction_group.name
        self.gaction_group.name = self.new_name
        self.new_name = old_name
        self.project.change_action_name(self.gaction_group)
