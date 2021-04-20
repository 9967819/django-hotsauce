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

from gazpacho.placeholder import Placeholder
from gazpacho.properties import prop_registry, CustomProperty, IntType
from gazpacho.gadget import Gadget
from gazpacho.widgets.base.base import ContainerAdaptor

class NotebookAdaptor(ContainerAdaptor):

    def _selection_changed_cb(self, selection, notebook):
        if not selection:
            return

        # Use the first widget that is embedded in the notebook
        for widget in selection:
            if widget.is_ancestor(notebook):
                break
        else:
            # No widget were embedded in us
            return

        # Now get the toplevel child embedded in the page
        while widget.get_parent() != notebook:
            widget = widget.get_parent()

        # Finally, if the page of that widget is different from the
        # currently selected one, switch to it
        widget_page = notebook.page_num(widget)
        if widget_page != notebook.get_current_page():
            notebook.set_current_page(widget_page)

    def _add_signal_handler(self, project, widget):
        project.selection.connect('selection-changed',
                                  self._selection_changed_cb, widget)

    def create(self, context, interactive=True):
        widget = super(NotebookAdaptor, self).create(context, interactive)
        self._add_signal_handler(context.get_project(), widget)
        return widget

    def load(self, context, widget):
        gadget = super(NotebookAdaptor, self).load(context, widget)
        self._add_signal_handler(context.get_project(), widget)
        return gadget

    def replace_child(self, context, current, new, container):
        page_num = container.page_num(current)
        if page_num == -1:
            return

        label = container.get_tab_label(current)

        container.remove_page(page_num)
        container.insert_page(new, label, page_num)

        new.show()
        container.set_current_page(page_num)


# GtkNotebook

class NPagesProp(CustomProperty, IntType):
    minimum = 1
    maximum = 100
    step_increment = 1
    page_increment = 1
    climb_rate = 1
    label = "Number of pages"
    default = 3
    persistent = False

    def load(self):
        self._initial = self.default

        # Don't set default if object has childs already
        if not self.get():
            self.set(self.default)

    def get(self):
        return self.object.get_n_pages()

    def set(self, value):
        old_size = self.object.get_n_pages()
        new_size = value
        if new_size == old_size:
            return

        if new_size > old_size:
            project = self._project
            # The notebook has grown. Add pages
            while new_size > old_size:
                label = gtk.Label()
                project.set_new_widget_name(label)

                #print load_gadget_from_widget(label, project)
                no = self.object.append_page(
                    Placeholder(), label)
                label.set_text('Page %d' % (no + 1))
                #project.add_widget(label)
                old_size += 1
        else:
            # The notebook has shrunk. Remove pages

            # Thing to remember is that GtkNotebook starts the
            # page numbers from 0, not 1 (C-style). So we need to do
            # old_size-1, where we're referring to "nth" widget.
            while old_size > new_size:
                child_widget = self.object.get_nth_page(old_size - 1)
                child_gadget = Gadget.from_widget(child_widget)
                # If we got it, and it's not a placeholder, remove it
                # from the project
                if child_gadget:
                    self._project.remove_widget(child_widget)

                self.object.remove_page(old_size - 1)
                old_size -= 1

prop_registry.override_property('GtkNotebook::n-pages', NPagesProp)

# Do not save property, since we need loader support since
# Gtk+ ignores the value of the property.
prop_registry.override_simple('GtkNotebook::page', persistent=False)

