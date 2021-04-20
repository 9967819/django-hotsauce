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

"""This module implements a Clipboard object to add support for
cut/copy/paste operations in Gazpacho.
It also defines a ClipboardWindow widget to graphically display and
select Clipboard data.

The Clipboard holds instances of ClipboardItems which contains information
of the widgets and a XML representation of them.
"""

import gobject
import gtk
from kiwi.utils import gsignal, type_register

from gazpacho import util

from gazpacho.command import FlipFlopCommandMixin, Command
from gazpacho.commandmanager import command_manager
from gazpacho.i18n import _

class ClipboardItem(object):
    """The ClipboardItem is the data that is stored in the
    clipboard. It contains an XML representation of the widget and
    some additional information that can be useful to know about
    without having to recreate the widget.."""

    def __init__(self, gadget):
        self.name = gadget.name
        self.icon = gadget.adaptor.icon.get_pixbuf()
        self.is_toplevel = gadget.is_toplevel()
        self.type = gadget.adaptor.type

        self._xml = gadget.to_xml(skip_external_references=True)

    def to_xml(self):
        return self._xml

class Clipboard(gobject.GObject):
    """The Clipboard is an abstraction Gazpacho uses to support
    cut/copy/paste operations. It's basically a container which
    holds XML representation of copied/cut widgets.

    So far it doesn't use X selection mechanism but it should
    not be dificult to add it in the future.
    """

    gsignal('widget-added', object)
    gsignal('widget-removed', object)
    gsignal('selection-changed', object)

    def __init__(self):
        gobject.GObject.__init__(self)

        # A list with the clipboard content. New items are added to
        # the end of the list.
        self.content = []

        # The currently selected item. If None we use the last item in
        # the content list instead.
        self._selected = None

        # We limit the maximum number of items in the clipboard
        # otherwise it would grow indefinitely. If to many items are
        # added the oldest will be removed.
        self._max_clipboard_items = 15

    def get_selected(self):
        return self._selected

    def set_selected(self, item):
        self._selected = item
        if not item and self.content:
            item = self.content[-1]
        self.emit('selection_changed', item)

    selected = property(get_selected, set_selected)

    def add_gadget(self, src_gadget):
        """Add a ClipboardItem wrapping the the source widget to the clipboard.
        A 'widget-added' signal is then emitted to indicate that there
        are new data on the clipboard. If the clipboard contains too
        many items the oldest item will be removed and a
        'widget-removed' signal emitted."""
        item = ClipboardItem(src_gadget)

        self.content.append(item)
        self.emit('widget-added', item)
        self.selected = item

        # Remove the oldest item if the clipboard contains too many
        # items
        if len(self.content) > self._max_clipboard_items:
            self._remove_oldest_item()

    def _remove_oldest_item(self):
        """Remove the oldest item from the clipboard."""
        if not self.content:
            return

        item_removed = self.content.pop(0)
        self.emit('widget-removed', item_removed)

    def get_selected_item(self):
        """Get the selected clipboard item."""
        if self.selected:
            return self._selected
        elif self.content:
            return self.content[-1]
        return None

    def get_selected_widget(self, project):
        """Get a widget instance from the selected item.

        This build a widget instance from the XML of the selected item.
        Before adding this to a project you should check that its name
        is unique
        """


        item = self.get_selected_item()
        if item is None:
            return

        from gazpacho.gadget import Gadget
        return Gadget.from_xml(project, item.to_xml(), item.name)

    # public methods for copy/cut/paste

    def copy(self, gadget):
        """Add a copy of the widget to the clipboard.

        Note that it does not make sense to undo this operation
        """
        # internal children cannot be copied. Shoulw we notify the user?
        if gadget.internal_name is not None:
            return

        self.add_gadget(gadget)

    def cut(self, gadget):
        # internal children cannot be cut. Should we notify the user?
        if gadget.internal_name is not None:
            return

        # add it to the clipboard
        self.add_gadget(gadget)

        project = gadget.project
        if isinstance(gadget.widget, gtk.TreeViewColumn):
            from gazpacho.util import get_parent
            from gazpacho.widgets.base.treeview import CommandAddRemoveTreeViewColumn
            tree_view = get_parent(gadget.widget)
            cmd = CommandAddRemoveTreeViewColumn(tree_view, gadget,
                                                 project, False)
        else:
            cmd = CommandCutPaste(gadget, project, None, True)

        command_manager.execute(cmd, project)

    def paste(self, placeholder, project):
        if project is None:
            raise ValueError("No project has been specified. Cannot paste "
                             "the widget")

        gadget = self.get_selected_widget(project)

        if (isinstance(placeholder, gtk.TreeView)
            and isinstance(gadget.widget, gtk.TreeViewColumn)):
            from gazpacho.gadget import Gadget
            from gazpacho.widgets.base.treeview import CommandAddRemoveTreeViewColumn
            tree_view = Gadget.from_widget(placeholder)
            cmd = CommandAddRemoveTreeViewColumn(tree_view, gadget,
                                                 project, True)
        else:
            cmd = CommandCutPaste(gadget, project, placeholder, False)

        command_manager.execute(cmd, project)
        return gadget

type_register(Clipboard)

clipboard = Clipboard()

class ClipboardWindow(gtk.Window):
    """ClipboardWindow is a Widget to represent and manage a Clipboard.

    It displays the current Clipboard contents through a TreeView.
    """

    ICON_COLUMN = 0
    NAME_COLUMN = 1
    WIDGET_COLUMN = 2

    def __init__(self, parent, clipboard):
        gtk.Window.__init__(self)
        self.set_title(_('Clipboard Contents'))
        self.set_transient_for(parent)

        self._clipboard = clipboard
        clipboard.connect('widget-added', self._widget_added_cb)
        clipboard.connect('widget-removed', self._widget_removed_cb)

        self._store = self._create_store(clipboard)
        self._store.connect('row-changed', self._row_changed_cb)

        self._view = self._create_view()
        self._view.get_selection().connect('changed',
                                           self._selection_changed_cb)
        self._view.connect('row-activated', self._row_activated_cb)
        self._set_default_selection()

        scroll = gtk.ScrolledWindow()
        scroll.set_size_request(300, 200)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self._view)
        self.add(scroll)

        self._view.show_all()

    def _create_store(self, clipboard):
        """Create a ListStore and fill it will items from the clipboard."""
        store = gtk.ListStore(gtk.gdk.Pixbuf, str, object)
        for clip_item in clipboard.content:
            store.append((clip_item.icon, clip_item.name, clip_item))
        return store

    def _create_view(self):
        """Create the tree view that will display the clipboard data."""
        view = gtk.TreeView(self._store)
        view.set_headers_visible(False)

        column = gtk.TreeViewColumn()
        renderer1 = gtk.CellRendererPixbuf()
        column.pack_start(renderer1, False)
        column.add_attribute(renderer1, 'pixbuf', ClipboardWindow.ICON_COLUMN)
        renderer2 = gtk.CellRendererText()
        column.pack_start(renderer2)
        column.add_attribute(renderer2, 'text', ClipboardWindow.NAME_COLUMN)

        view.append_column(column)
        return view

    def _set_clipboard_selection(self):
        """Notify the Clipboard about which item is currently selected."""
        (model, it) = self._view.get_selection().get_selected()
        if it:
            clip_item = model[it][ClipboardWindow.WIDGET_COLUMN]
            self._clipboard.selected = clip_item

    def _selection_changed_cb(self, selection, data=None):
        """Callback for selection changes in the tree view."""
        self._set_clipboard_selection()

    def _widget_added_cb(self, clipboard, new_item):
        """Callback that is triggered when an item is added to the
        clipboard."""
        self._store.append((new_item.icon, new_item.name, new_item))

    def _widget_removed_cb(self, clipboard, old_item):
        """Callback that is triggered when an item is removed from the
        clipboard."""
        # It's always the oldes item that is removed so we can just
        # remove the first item from the store.
        first_iter = self._store.get_iter_first()
        if first_iter:
            self._store.remove(first_iter)

    def _row_changed_cb(self, model, path, new_iter, data=None):
        """Callback that is called when rows are added or removed."""
        self._set_default_selection()

    def _set_default_selection(self):
        """Set the default selection, i.e. the latest additiion."""
        last_iter = get_last_iter(self._store)
        if last_iter:
            self._view.get_selection().select_iter(last_iter)

    def _row_activated_cb(self, treeview, path, column):
        item = self._store[path][2]
        print('The current item is represented by:')
        print(item.to_xml())

    def hide_window(self):
        """Hide the clipboard window."""
        self.hide()
        self._clipboard.selected = None

    def show_window(self):
        """Show the clipboard window."""
        self.show_all()
        self._set_default_selection()

def get_last_iter(model):
    """Convenient function to get the last iterator from a tree model."""
    items = len(model)
    if items > 0:
        return model.iter_nth_child(None, items - 1)
    return None


class CommandCutPaste(FlipFlopCommandMixin, Command):

    def __init__(self, gadget, project, placeholder, cut):
        FlipFlopCommandMixin.__init__(self, cut)

        if cut:
            description = _('Cut widget %s into the clipboard') % gadget.name
        else:
            description = _('Paste widget %s from the clipboard') % gadget.name
        Command.__init__(self, description)

        self._project = project
        self._placeholder = placeholder
        self._gadget = gadget

    def _execute_cut(self):
        from gazpacho.gadget import Gadget
        from gazpacho.placeholder import Placeholder

        gadget = self._gadget

        if not gadget.is_toplevel():
            parent = gadget.get_parent()

            if not self._placeholder:
                self._placeholder = Placeholder()

            Gadget.replace(gadget.widget,
                           self._placeholder, parent)

        gadget.widget.hide()
        gadget.project.remove_widget(gadget.widget)
        gadget.deleted = True

    _execute_state1 = _execute_cut

    def _execute_paste(self):
        # Note that updating the dependencies might replace the
        # widget's gtk-widget so we need to make sure we refer to the
        # correct one afterward.
        from gazpacho.gadget import Gadget
        self._gadget.deleted = False

        if self._gadget.is_toplevel():
            project = self._project
        else:
            parent = util.get_parent(self._placeholder)
            project = parent.project
            Gadget.replace(self._placeholder,
                           self._gadget.widget,
                           parent)

        project.add_widget(self._gadget.widget, new_name=True)
        self._gadget.select()

        self._gadget.widget.show_all()

        # We need to store the project of a toplevel widget to use
        # when undoing the cut.
        self._project = project

        return self._gadget

    _execute_state2 = _execute_paste
