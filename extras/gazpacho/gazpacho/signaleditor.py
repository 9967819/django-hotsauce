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
import pango
from kiwi.utils import gsignal, type_register

from gazpacho.command import Command
from gazpacho.commandmanager import command_manager
from gazpacho.i18n import _

(MODE_NOTHING,
 MODE_ADD,
 MODE_REMOVE,
 MODE_CHANGE) = list(range(4))

(COLUMN_SIGNAL,
 COLUMN_HANDLER,
 COLUMN_AFTER,
 COLUMN_AFTER_VISIBLE,
 COLUMN_HANDLER_EDITABLE,
 COLUMN_SLOT,
 COLUMN_OBJECT,
 COLUMN_BOLD) = list(range(8))

class SignalInfo(object):
    """
    This class encapsulates information about a signal handler.

    In addition to the actual handler information this class also
    stores the handler name in a normalized form where all underscores
    have been replaced with dashes. For example, if the name is
    'my_signal' the normalized name will be 'my-signal'. When
    comparing SignalInfo instances this will be based on the
    normalized name and not the name.

    @cvar name:
    @cvar normalized_name:
    @cvar handler:
    @cvar after:
    @cvar object: object
    """
    def __init__(self, name, handler, after=False, object=''):
        if not isinstance(name, str):
            raise TypeError("name must be a string not %r" % name)
        self.name = name
        self.normalized_name = name.replace('_', '-')
        if handler is not None and not isinstance(handler, str):
            raise TypeError(
                "handler must be a string or None, not %r" % handler)
        self.handler = handler
        if not isinstance(after, bool):
            raise TypeError("after must be a bool, not %r" % after)
        self.after = after
        if object is not None and not isinstance(object, str):
            raise TypeError("object must be a string or None, not %r" % object)
        self.object = object

    def copy(self):
        return self.__class__(name=self.name, handler=self.handler,
                              after=self.after, object=self.object)

    def __repr__(self):
        return '<SignalInfo name=%s, handler=%s %s %s>' % (self.name,
                                                           self.handler,
                                                           self.after,
                                                           self.object)

    def __eq__(self, other):
        """
        Compare if two SignalInfo instance are considered equal. Note
        that this is not based on the handler name but the normalized
        name.
        """
        if not isinstance(other, self.__class__):
            return False
        if ((self.normalized_name, self.handler, self.after, self.object) !=
            (other.normalized_name, other.handler, other.after, other.object)):
            return False
        return True

SLOT_MESSAGE = _("<Type the signal's handler here>")

class SignalEditor(gtk.VBox):
    """ The GladeSignalEditor is used to house the signal editor interface and
    associated functionality """

    gsignal('signal-activated', object, str)

    def __init__(self, editor, app):
        gtk.VBox.__init__(self)

        self._editor = editor
        self._app = app
        self._model = None
        self._gadget = None
        self._adaptor = None
        self._model = gtk.TreeStore(str, str, bool, bool,
                                    bool, bool, str, bool)
        self._treeview = self._construct_signal_list(self._model)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(self._treeview)
        self.pack_start(scroll)
        self.show_all()

    def load_gadget(self, gadget):
        """
        Loads all the signals from the gadget and displays them in the view

        @param gadget: a L{gazpacho.gadget.Widget} instance
        """
        self._gadget = gadget
        self._adaptor = gadget and gadget.adaptor or None

        self._internal_load(gadget)

    def _construct_signal_list(self, model):
        view = gtk.TreeView(model)
        view.connect('row-activated', self._treeview_row_activated_cb)
        view.connect('key-press-event', self._treeview_key_press_event_cb)
        view.connect('button-press-event', self._treeview_button_press_event_cb)

        # signal column
        renderer = gtk.CellRendererText()
        renderer.set_property('weight', pango.WEIGHT_BOLD)
        column = gtk.TreeViewColumn(_('Signal'), renderer, text=COLUMN_SIGNAL,
                                    weight_set=COLUMN_BOLD)
        view.append_column(column)

        # handler column
        renderer = gtk.CellRendererText()
        renderer.set_property('style', pango.STYLE_ITALIC)
        renderer.set_property('foreground', 'Gray')
        renderer.connect('edited', self._handler_cell_edited_cb)
        column = gtk.TreeViewColumn(_('Handler'), renderer,
                                    text=COLUMN_HANDLER,
                                    style_set=COLUMN_SLOT,
                                    foreground_set=COLUMN_SLOT,
                                    editable=COLUMN_HANDLER_EDITABLE)
        view.append_column(column)

        # after column
        renderer = gtk.CellRendererToggle()
        renderer.connect('toggled', self._after_cell_toggled_cb)
        column = gtk.TreeViewColumn(_('After'), renderer,
                                    active=COLUMN_AFTER,
                                    visible=COLUMN_AFTER_VISIBLE)
        view.append_column(column)

        # object column
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self._object_cell_edited_cb)
        column = gtk.TreeViewColumn(_('Object'), renderer,
                                    editable=COLUMN_HANDLER_EDITABLE,
                                    text=COLUMN_OBJECT,
                                    visible=COLUMN_AFTER_VISIBLE)
        view.append_column(column)

        return view

    def _internal_load(self, gadget):
        model = self._model
        model.clear()

        if not gadget:
            return

        last_type = ""
        parent_class = None
        for signal_name, signal_type in self._adaptor.list_signals():
            if signal_type != last_type:
                parent_class = model.append(None)
                model.set(parent_class,
                          COLUMN_SIGNAL, signal_type,
                          COLUMN_AFTER_VISIBLE, False,
                          COLUMN_HANDLER_EDITABLE, False,
                          COLUMN_SLOT, False,
                          COLUMN_BOLD, False)
                last_type = signal_type

            parent_signal = model.append(parent_class)
            signals = gadget.list_signal_handlers(signal_name)

            if not signals:
                model.set(parent_signal,
                          COLUMN_SIGNAL, signal_name,
                          COLUMN_HANDLER, SLOT_MESSAGE,
                          COLUMN_AFTER, False,
                          COLUMN_HANDLER_EDITABLE, True,
                          COLUMN_AFTER_VISIBLE, False,
                          COLUMN_SLOT, True)
            else:
                gadget_signal = signals[0]
                model.set(parent_signal,
                          COLUMN_BOLD, True,
                          COLUMN_SIGNAL, signal_name,
                          COLUMN_HANDLER, gadget_signal.handler,
                          COLUMN_AFTER, gadget_signal.after,
                          COLUMN_OBJECT, gadget_signal.object,
                          COLUMN_AFTER_VISIBLE, True,
                          COLUMN_HANDLER_EDITABLE, True,
                          COLUMN_SLOT, False)
                self._treeview.expand_row(model[parent_class].path, False)

                for widget_signal in signals[1:]:
                    model.set(model.append(parent_signal),
                              COLUMN_HANDLER, widget_signal.handler,
                              COLUMN_AFTER, widget_signal.after,
                              COLUMN_OBJECT, widget_signal.object,
                              COLUMN_AFTER_VISIBLE, True,
                              COLUMN_HANDLER_EDITABLE, True,
                              COLUMN_SLOT, False)

                # add the <Type...> slot
                model.set(model.append(parent_signal),
                          COLUMN_HANDLER, SLOT_MESSAGE,
                          COLUMN_AFTER, False,
                          COLUMN_OBJECT, '',
                          COLUMN_AFTER_VISIBLE, False,
                          COLUMN_HANDLER_EDITABLE, True,
                          COLUMN_SLOT, True)

        self._treeview.expand_row((0,), False)

    def _is_valid_identifier(self, text):
        if text is None:
            return False

        return True

    def _append_slot(self, iter_signal):
        model = self._model
        model.set(model.append(iter_signal),
                  COLUMN_HANDLER, SLOT_MESSAGE,
                  COLUMN_AFTER, False,
                  COLUMN_OBJECT, '',
                  COLUMN_AFTER_VISIBLE, False,
                  COLUMN_HANDLER_EDITABLE, True,
                  COLUMN_SLOT, True)

        # mark the signal and class name as bold
        row = model[iter_signal]
        row[COLUMN_BOLD] = True
        row.parent[COLUMN_BOLD] = True

    def _remove_row(self, model_iter):
        "Remove a row from the signal tree"
        model = self._model
        # if this isn't the first row we can just remove it
        signal_name = model[model_iter][COLUMN_SIGNAL]
        if signal_name is None:
            model.remove(model_iter)
            return

        # We cannot delete the first row so we have to copy the next
        # row and delete that instead
        next_iter = model.iter_nth_child(model_iter, 0)
        if not next_iter:
            return

        (handler, after, visible,
         editable, slot, obj) = tuple(model[next_iter])[1:7]
        row = model[model_iter]
        row[COLUMN_HANDLER] = handler
        row[COLUMN_AFTER] = after
        row[COLUMN_AFTER_VISIBLE] = visible
        row[COLUMN_HANDLER_EDITABLE] = editable
        row[COLUMN_OBJECT] = obj
        row[COLUMN_SLOT] = slot

        next_iter = model.remove(next_iter)

        # if last signal handler was removed, the parents has to be updated
        # to reflect this
        if not next_iter:
            row = model[model_iter]
            row[COLUMN_BOLD] = False

            # We need to go through all children of the signal class
            # and see if any of them are bold and update the class node
            # to reflect this
            bold = False
            for child in row.parent.iterchildren():
                bold = child[COLUMN_BOLD]
                if bold:
                    break

            row.parent[COLUMN_BOLD] = bold

    def _is_row_deletable(self, model_iter):
        """Check whether a row can be deleted or not."""
        row = self._model[model_iter]
        return row[COLUMN_HANDLER_EDITABLE] and not row[COLUMN_SLOT]

    def _remove_signal_handler(self, model_iter):
        """Remove signal handler both from the treeview and the widget."""
        row = self._model[model_iter]
        signal_name = row[COLUMN_SIGNAL]
        if signal_name is None:
            signal_name = row.parent[COLUMN_SIGNAL]

        signal = SignalInfo(name=signal_name,
                            handler=row[COLUMN_HANDLER],
                            after=row[COLUMN_AFTER],
                            object=row[COLUMN_OBJECT])
        cmd = CommandAddRemoveSignal(self._gadget, signal, False)
        command_manager.execute(cmd, self._gadget.project)
        self._remove_row(model_iter)

    def _create_popup(self, item_iter):
        def _popup_delete_activate_cb(item, item_iter):
            self._remove_signal_handler(item_iter)

        menu = gtk.Menu()
        menu_item = gtk.ImageMenuItem(gtk.STOCK_DELETE, None)
        menu_item.connect('activate', _popup_delete_activate_cb, item_iter)
        menu_item.show()
        menu.append(menu_item)
        return menu

    def _is_void_signal_handler(self, signal_handler):
        return (signal_handler is None or
                signal_handler.strip() == '' or
                signal_handler == SLOT_MESSAGE)

    def _handler_cell_edited_cb(self, cell, path_str, new_handler):
        if (self._model[path_str][COLUMN_SLOT] and
            self._is_void_signal_handler(new_handler)):
            return
        self._change(path_str, handler=new_handler)

    def _object_cell_edited_cb(self, cell, path_str, obj):
        if self._model[path_str][COLUMN_SLOT] and not obj:
            return
        self._change(path_str, obj=obj)

    def _change(self, path, handler=None, obj=None):
        if handler is None and obj is None:
            raise TypeError

        model = self._model
        model_iter = model[path].iter
        (signal_name, old_handler,
         after, slot, old_object) = model.get(model_iter,
                                              COLUMN_SIGNAL, COLUMN_HANDLER,
                                              COLUMN_AFTER, COLUMN_SLOT,
                                              COLUMN_OBJECT)
        if signal_name is None:
            row = model[model_iter]
            signal_name = row.parent[COLUMN_SIGNAL]
            iter_signal = row.parent.iter
        else:
            iter_signal = model_iter

        signal = SignalInfo(name=signal_name, handler=handler,
                            after=after, object=obj)

        if handler:
            is_void = (handler is None or
                       handler.strip() == '' or
                       handler == SLOT_MESSAGE)
        elif obj:
            is_void = (obj is None or obj.strip() == '')
        else:
            return

        if slot and not is_void:
            mode = MODE_ADD
        if not slot and is_void:
            mode = MODE_REMOVE
        if not slot and not is_void:
            mode = MODE_CHANGE

        # we are adding a new handler
        if mode == MODE_ADD:
            signal.after = False
            cmd = CommandAddRemoveSignal(self._gadget, signal, True)
            command_manager.execute(cmd, self._gadget.project)
            row = model[model_iter]
            row[COLUMN_SLOT] = False
            row[COLUMN_HANDLER] = handler
            row[COLUMN_AFTER_VISIBLE] = True
            row[COLUMN_OBJECT] = obj
            # append a <Type...> slot
            self._append_slot(iter_signal)

        # we are removing a signal handler
        if mode == MODE_REMOVE:
            signal.handler = old_handler
            signal.object = old_object
            cmd = CommandAddRemoveSignal(self._gadget, signal, False)
            command_manager.execute(cmd, self._gadget.project)
            self._remove_row(model_iter)
            return

        # we are changing a signal handler
        if mode == MODE_CHANGE:
            old_signal = signal.copy()
            old_signal.handler = old_handler
            old_signal.object = old_object
            if object:
                signal.handler = handler
            if handler:
                signal.object = obj
            row = model[model_iter]
            row[COLUMN_SLOT] = False
            row[COLUMN_HANDLER] = signal.handler
            row[COLUMN_AFTER_VISIBLE] = True
            row[COLUMN_OBJECT] = signal.object
            cmd = CommandChangeSignal(self._gadget, old_signal, signal)
            command_manager.execute(cmd, self._gadget.project)

    def _after_cell_toggled_cb(self, cell, path_str, data=None):
        model = self._model
        row = model[path_str]
        signal_name = row[COLUMN_SIGNAL]
        if signal_name is None:
            signal_name = row.parent[COLUMN_SIGNAL]
        handler = row[COLUMN_HANDLER]
        after = row[COLUMN_AFTER]
        obj = row[COLUMN_OBJECT]

        old_signal = SignalInfo(name=signal_name, object=obj,
                                handler=handler, after=after)
        new_signal = SignalInfo(name=signal_name, object=obj,
                                handler=handler, after=not after)

        cmd = CommandChangeSignal(self._gadget, old_signal, new_signal)
        command_manager.execute(cmd, self._gadget.project)

        row[COLUMN_AFTER] = not after

    def _treeview_row_activated_cb(self, view, path, column, data=None):
        view.set_cursor(path, column, True)
        view.grab_focus()
        self.emit('signal-activated', self._gadget,
                  self._model[path][COLUMN_SIGNAL])

    def _treeview_key_press_event_cb(self, view, event):
        if not event.keyval in (gtk.keysyms.Delete, gtk.keysyms.KP_Delete):
            return

        model_iter = view.get_selection().get_selected()[1]
        if self._is_row_deletable(model_iter):
            self._remove_signal_handler(model_iter)

    def _treeview_button_press_event_cb(self, view, event):
        if event.button != 3:
            return False

        result = view.get_path_at_pos(int(event.x), int(event.y))
        if not result:
            return False
        path = result[0]
        item_iter = self._model[path].iter

        if self._is_row_deletable(item_iter):
            view.set_cursor(path)
            view.grab_focus()
            popup = self._create_popup(item_iter)
            popup.popup(None, None, None, event.button, event.time)
            return True

        return False

type_register(SignalEditor)

# signal command
class CommandAddRemoveSignal(Command):
    def __init__(self, gadget, signal, add):
        if add:
            description = _('Add signal handler %s') % signal.handler
        else:
            description = _('Remove signal handler %s') % signal.handler

        Command.__init__(self, description)
        self._add = add
        self._signal = signal
        self._gadget = gadget

    def execute(self):
        if self._add:
            self._gadget.add_signal_handler(self._signal)
        else:
            self._gadget.remove_signal_handler(self._signal)

        self._add = not self._add

class CommandChangeSignal(Command):
    def __init__(self, gadget, old_signal_handler, new_signal_handler):
        description = _('Change signal handler for signal "%s"') % \
                      old_signal_handler.name
        Command.__init__(self, description)
        self._gadget = gadget
        self._old_handler = old_signal_handler
        self._new_handler = new_signal_handler

    def execute(self):
        self._gadget.change_signal_handler(self._old_handler,
                                                    self._new_handler)
        self._old_handler, self._new_handler = (self._new_handler,
                                                self._old_handler)
