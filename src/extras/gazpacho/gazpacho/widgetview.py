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

from kiwi.utils import gsignal

from gazpacho.app.bars import bar_manager
from gazpacho.commandmanager import command_manager
from gazpacho.popup import Popup
from gazpacho.gadget import Gadget
from gazpacho.util import select_iter, get_all_children
from gazpacho.signalhandlers import SignalHandlerStorage

(GADGET_COLUMN, N_COLUMNS) = list(range(2))
COLUMN_TYPES = [object]

class WidgetTreeView(gtk.ScrolledWindow):
    gsignal('selection-changed', object)
    def __init__(self, app):
        gtk.ScrolledWindow.__init__(self)

        self._app = app

        self.set_shadow_type(gtk.SHADOW_IN)

        self._project = None

        # We need to know the signal id which we are connected to so
        # that when the project changes we stop listening to the old
        # project
        self._handlers = SignalHandlerStorage()

        # The model
        self._model = gtk.TreeStore(*COLUMN_TYPES)

        # The view
        self._tree_view = gtk.TreeView(self._model)
        self._tree_view.connect('row-activated',
                                self._on_treeview_row_activated)
        self._tree_view.connect('key-press-event', self._on_treeview_key_press)
        #self._tree_view.connect('motion-notify-event', self._motion_notify_cb)
        self._tree_view.connect('button-press-event',
                                self._on_treeview_button_press)
        self._tree_view.set_headers_visible(False)
        self._tree_view.show()

        self._tree_selection = self._tree_view.get_selection()
        self._tree_selection.connect('changed', self._on_treeselection_changed)
        self._tree_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self._add_columns()

        # True when we are going to set the project selection. So that
        # we don't recurse cause we are also listening for the project
        # changed selection signal
        self._updating_selection = False

        self.add(self._tree_view)

    #
    # Public methods
    #

    def set_project(self, project):
        """
        Set the current project.

        @param project: the current project
        @type project: L{gazpacho.project.Project}
        """
        if project == self._project:
            return
        # Thie view stops listening to the old project(if there was one)
        if self._project:
            self._handlers.disconnect_all()

        # Set to null while we remove all the items from the store,
        # because we are going to trigger selection_changed signal
        # emisions on the View. By setting the project to None,
        # _on_treeselection_changed will just return
        self._project = None

        self._model.clear()

        # if we were passed None we are done
        if not project:
            return

        self._project = project
        self._populate_model()

        # Here we connect to all the signals of the project that interest us
        self._handlers.connect(project, 'add-gadget',
                               self._on_project_add_gadget)
        self._handlers.connect(project, 'remove-gadget',
                               self._on_project_remove_gadget)
        self._handlers.connect(project, 'gadget-name-changed',
                               self._on_project_gadget_name_changed)
        self._handlers.connect(project.selection, 'selection-changed',
                               self._on_selection_changed)

    #
    # Private methods
    #

    def _populate_model(self):
        if not self._project:
            return

        # add the widgets and recurse
        self._populate_model_real(self._project.get_windows(), None, True)

    def _populate_model_real(self, widgets, parent_iter, add_children):
        for w in widgets:
            iter = parent_iter
            gadget = Gadget.from_widget(w)
            if gadget:
                iter = self._model.append(parent_iter, (gadget,))
                if add_children:
                    children = gadget.get_children()
                    self._populate_model_real(children, iter, True)

    def _add_columns(self):
        column = gtk.TreeViewColumn()
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, self._view_cell_function, True)

        renderer = gtk.CellRendererText()
        column.pack_start(renderer)
        column.set_cell_data_func(renderer, self._view_cell_function, False)

        self._tree_view.append_column(column)

    def _view_cell_function(self, tree_column, cell, model, iter, is_icon):
        widget = model[iter][GADGET_COLUMN]
        if not widget:
            return

        if is_icon:
            if widget.adaptor.pixbuf:
                cell.set_property('pixbuf', widget.adaptor.pixbuf)
            else:
                cell.set_property('pixbuf', None)
        else:
            cell.set_property('text', widget.name)

    def _find_iter(self, iter, findme):
        next = iter
        while next:
            gadget = self._model[next][GADGET_COLUMN]
            if not gadget:
                print ('Could not get the gadget from the model')

            # Check for widget wrapper and real widgets
            if gadget == findme or gadget.widget == findme:
                return next

            if self._model.iter_has_child(next):
                child = self._model.iter_children(next)
                retval = self._find_iter(child, findme)
                if retval:
                    return retval

            next = self._model.iter_next(next)

        return None

    def _find_iter_by_widget(self, widget):
        root = self._model.get_iter_root()
        return self._find_iter(root, widget)

    def _add_children(self, parent, parent_iter):
        """ This function is needed because sometimes when adding a widget
        to the tree their children are not added.

        Please note that not all widget has a gadget associated with them
        so there are some special cases we need to handle."""
        parent_gadget = Gadget.from_widget(parent)
        if parent_gadget:
            children = parent_gadget.get_children()
        else:
            children = get_all_children(parent)

        for child in children:
            gadget = Gadget.from_widget(child)
            if not gadget:
                if isinstance(child, gtk.Container):
                    self._add_children(child, parent_iter)
                else:
                    continue

            elif not self._find_iter(parent_iter, gadget):
                child_iter = self._model.append(parent_iter, (gadget,))
                self._add_children(child, child_iter)

    def _get_selected_gadgets(self):
        """
        Get a list of the gadgets selected in the widget tree.

        @return: list of selected gadgets
        @rtype list (of L{gazpacho.gadget.Gadget})
        """
        if not self._project:
            return []

        # There are no cells selected
        model, iters = self._tree_selection.get_selected_rows()
        gadgets = []
        for iter in iters:
            gadget = model[iter][GADGET_COLUMN]
	    # Workaround for bug #344275
            if gadget:
                gadgets.append(gadget)
        return gadgets

    #
    # Signal handlers
    #

    def _on_treeview_button_press(self, view, event):
        """
        Show the context menu on a right click.
        """
        if not self._project:
            return False

        if event.button != 3:
            return False

        result = view.get_path_at_pos(int(event.x), int(event.y))
        if not result:
            return False
        path = result[0]
        row = self._model[path]
        widget = row[GADGET_COLUMN]
        select_iter(self._tree_view, row.iter)

        popup = Popup(command_manager, widget)
        popup.pop(event)
        return True

    def _on_treeselection_changed(self, selection):
        """
        Update the widget selection when the selection in the treeview
        changes.
        """
        # the project might not be set when the treeview is modified
        if not self._project:
            return

        # we are already trying to update the selection, no need to do
        # it again.
        if self._updating_selection:
            return

        gadgets = self._get_selected_gadgets()
        self.emit('selection-changed', gadgets)

        self._updating_selection = True

        self._project.selection.clear(False)
        for gadget in gadgets:
            self._project.selection.add(gadget.widget, False)
        self._project.selection.selection_changed()
        self._updating_selection = False

    def _on_treeview_row_activated(self, treeview, path, column):
        """
        Show the toplevel widget to which the widget on the activated
        row belongs.
        """
        gadget = self._model[path][GADGET_COLUMN]
        toplevel = gadget.widget.get_toplevel()
        toplevel.show_all()
        toplevel.present()

    def _on_treeview_key_press(self, view, event):
        """
        Delete the selected gadget if the delete key has been pressed.
        """
        if event.keyval in (gtk.keysyms.Delete, gtk.keysyms.KP_Delete):
            bar_manager.activate_action('Delete')

    def _on_project_add_gadget(self, project, gadget):
        """
        When the widget is added to the project it should be added to
        the widget tree as well.
        """
        parent = gadget.get_parent()
        parent_iter = None
        if parent:
            parent_iter = self._find_iter_by_widget(parent)

        # When creating a widget with internal children (e.g. GtkDialog) the
        # children are added first so they do have a gadget parent but
        # don't have a parent_iter (since the parent has not being added yet
        if not parent_iter and parent:
            # we need to add this widget when adding the parent
            return

        gadget_iter = self._model.append(parent_iter, (gadget,))

        # now check for every children of this widget if it is already on the
        # tree. If not we add it.
        self._add_children(gadget.widget, gadget_iter)

        self._updating_selection = True
        gadget.select()
        self._updating_selection = False

        select_iter(self._tree_view, gadget_iter)

    def _on_project_remove_gadget(self, project, gadget):
        """
        Remove the widget from the widget tree when it's removed from
        the project.
        """
        iter = self._find_iter_by_widget(gadget)
        if iter:
            self._model.remove(iter)

    def _on_project_gadget_name_changed(self, project, widget):
        """
        Update the name of the widget in the widget tree when the name
        of the widget is changed.
        """
        treeiter = self._find_iter_by_widget(widget)
        # TODO: Figure out why treeiter is None here, it happens under
        #       unknown circumstances, see bug 333034
        if treeiter:
            model = self._model
            model.row_changed(model[treeiter].path, treeiter)

    def _on_selection_changed(self, selection):
        """
        Update the widget tree when the widget selection changes.
        """
        if self._updating_selection:
            return

        self._updating_selection = True

        self._tree_selection.unselect_all()
        for widget in selection:
            gadget_iter = self._find_iter_by_widget(widget)
            if gadget_iter:
                select_iter(self._tree_view, gadget_iter)

        self._updating_selection = False

    # This is not working anyway because the current
    # button_press_event code is not creating the widget when you
    # click on a parent having a palette button selected
    #
    #def _motion_notify_cb(self, view, event):
    #    if pw.project_window is None:
    #        cursor.set_for_widget_adaptor(event.window, None)
    #    else:
    #        cursor.set_for_widget_adaptor(event.window,
    #                                      pw.project_window.add_class)
    #
    #    return False

gobject.type_register(WidgetTreeView)
