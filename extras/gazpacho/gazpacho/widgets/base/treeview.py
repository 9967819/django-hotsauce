# Copyright (C) 2005 by SICEm S.L. and Async Open Source
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

import gobject
import gtk

from kiwi.ui.dialogs import BaseDialog

from gazpacho.command import FlipFlopCommandMixin, Command
from gazpacho.commandmanager import command_manager
from gazpacho.i18n import _
from gazpacho.model import ModelEditorDialog, GazpachoModel, renderer_expert
from gazpacho.properties import prop_registry, CustomProperty, StringType, \
     TransparentProperty
from gazpacho.propertyeditor import PropertyCustomEditorWithDialog, \
     PropertyEditorDialog
from gazpacho.gadget import Gadget, load_gadget_from_widget
from gazpacho.widgetadaptor import WidgetAdaptor, CreationCancelled
from gazpacho.widgetregistry import widget_registry
from gazpacho.widgets.base.base import ContainerAdaptor

class TreeViewAdaptor(ContainerAdaptor):
    # note that the treeview does not have a real model until a column is
    # added to it
    def create(self, context, interactive=True):
        # add a model to the project
        project = context.get_project()
        model = project.model_manager.create_model()

        # this (empty) model is needed to show the '+' column
        tree_view = gtk.TreeView(model.get_model())

        self._add_adder_column(tree_view)

        return tree_view

    def fill_empty(self, context, widget):
        pass

    def _on_add(self, column, gtk_tree_view):
        gadget = Gadget.from_widget(gtk_tree_view)
        self.add_tree_view_column(gadget, True)

    def add_tree_view_column(self, tree_view, interactive=True):
        adaptor = widget_registry.get_by_type(gtk.TreeViewColumn)
        project = tree_view.project
        try:
            column = Gadget(adaptor, project)
            column.create_widget(interactive)
        except CreationCancelled:
            return

        cmd = CommandAddRemoveTreeViewColumn(tree_view, column, project, True)
        command_manager.execute(cmd, project)
        return column

    def _add_adder_column(self, widget):
        col = gtk.TreeViewColumn()
        image = gtk.Image()
        image.show()
        image.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        col.set_widget(image)
        col.set_clickable(True)
        col.set_reorderable(False)
        col.connect('clicked', self._on_add, widget)
        widget.append_column(col)

    def get_children(self, context, tree_view):
        return [c for c in tree_view.get_columns() \
                if isinstance(c, GazpachoTreeViewColumn)]

    def load(self, context, tree_view):
        project = context.get_project()
        model = tree_view.get_model()
        gzmodel = None
        if model:
            gzmodel = project.model_manager.get_model(model.name)

        gadget = Gadget.load(tree_view, project)

        if gzmodel:
            gadget.widget.set_model(gzmodel.get_model())

        for column in tree_view.get_columns():
            load_gadget_from_widget(column, project)

        self._add_adder_column(tree_view)

        return gadget

    def replace_child(self, context, current, new, container):
        # don't put placeholders in the columns
        container.remove_column(current)

    def add_child(self, tree_view, column):
        cols = len(tree_view.widget.get_columns())
        column.widget.set_widget(None)
        tree_view.widget.insert_column(column.widget, cols - 1)
        column.widget.update_widget()

        # update the model with this column
        self.update_model_with_column(tree_view, column)

    def remove_child(self, tree_view, column):
        index = self.get_column_index(tree_view, column)
        tree_view.widget.remove_column(column.widget)

        self.update_model_with_column(tree_view, column, False)

        offset = len(column.widget.get_cell_renderers())
        self.update_other_columns_attributes(tree_view, -offset, index)

    def update_model_with_column(self, tree_view, column, adding=True):
        model = self.get_model(tree_view)

        if adding:
            model.add_columns_for_tree_view_column(column.widget)
        else:
            model.remove_columns_of_tree_view_column(column.widget)

        tree_view.widget.set_model(model.get_model())

    def before_change_column_layout(self, tree_view, column):
        """Remove the column renderers from the model"""
        index = self.get_column_index(tree_view, column)
        self.update_model_with_column(tree_view, column, False)

        offset = len(column.widget.get_cell_renderers())
        self.update_other_columns_attributes(tree_view, -offset, index)

    def after_change_column_layout(self, tree_view, column):
        """Inset the column renderers to the model at the offset
        this column is"""
        index = self.get_column_index(tree_view, column)
        cells = 0
        for i in range(index):
            col = tree_view.widget.get_column(i)
            cells += len(col.get_cell_renderers())

        # we update the model by *inserting* the types (not appending)
        model = self.get_model(tree_view)
        model.insert_columns_of_tree_view_column(column.widget, cells)
        tree_view.widget.set_model(model.get_model())

        # not we shift the attributes value of the renderers that are after the
        # ones of the column
        offset = len(column.widget.get_cell_renderers())
        self.update_other_columns_attributes(tree_view, offset, index + 1)

    def update_other_columns_attributes(self, tree_view, offset, column_index):
        """When removing a column from the model all other columns that are
        after it will have their attributes wrong (e.g. text=3 will be text=2)
        """
        # the last column is the adder column and we don't use it
        columns = tree_view.widget.get_columns()[column_index:-1]
        for c in columns:
            c.update_attributes(offset)

    def get_column_index(self, tree_view, column):
        """Return the index of column inside tree_view"""
        for i, col in enumerate(tree_view.widget.get_columns()):
            if col is column.widget:
                return i

    def get_model(self, tree_view):
        return GazpachoModel.from_model(tree_view.widget.get_model())

    def delete(self, context, widget):        
        model = GazpachoModel.from_model(widget.get_model())
        context.get_project().model_manager.remove_model(model)
        return model

    def restore(self, context, widget, model):
        context.get_project().model_manager.add_model(model)

# Disable headers-clickable, see bug #163851
prop_registry.override_simple('GtkTreeView::headers-clickable', enabled=False)

class ModelPropEditor(PropertyCustomEditorWithDialog):
    dialog_class = ModelEditorDialog
    button_text = _('Edit Model...')

class ModelAdaptor(CustomProperty, StringType):
    """This represents a fake property to edit the model of a TreeView"""
    custom_editor = ModelPropEditor
    translatable = False

    def get(self):
        model = self.object.get_model()
        if model:
            gzmodel = GazpachoModel.from_model(model)
            return gzmodel.get_name()

    def save(self):
        return self.get()

prop_registry.override_simple('GtkTreeView::model', ModelAdaptor)

class CellsDialogMixin(object):
    """This mixin provides common functionality to dialogs working with
    cell layouts

    It create widgets and add it to self.vbox so this widget should exist in
    the base class (as in dialogs)
    """

    def _make_layout_style(self, group, label, size_group):
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        rb = gtk.RadioButton(group, label)
        size_group.add_widget(rb)
        hbox.pack_start(rb, False, False)
        fr = gtk.Frame()
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, eb.style.white)
        cv = gtk.CellView()
        eb.add(cv)
        fr.add(eb)
        hbox.pack_start(fr, True, True)
        self.vbox.pack_start(hbox, False, False)
        return rb, cv

    def _create_widgets(self):
        title = gtk.Label()
        title.set_markup('<span size="larger" weight="bold">%s</span>' % \
                         _('Layout style'))
        self.vbox.pack_start(title, False, False)

        # with the size group we don't need a table to align the labels on
        # the left column
        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        group = None
        self.text_only, cell = self._make_layout_style(group,
                                                       _("Text only"),
                                                       size_group)
        group = self.text_only
        renderer = gtk.CellRendererText()
        renderer.set_property('markup', 'Text')
        cell.pack_start(renderer)

        self.image_text, cell = self._make_layout_style(group,
                                                        _("Image and text"),
                                                        size_group)
        renderer = gtk.CellRendererPixbuf()
        renderer.set_property('stock-id', gtk.STOCK_OK)
        renderer.set_property('stock-size', gtk.ICON_SIZE_MENU)
        cell.pack_start(renderer, expand=False)
        renderer = gtk.CellRendererText()
        renderer.set_property('markup', 'Text')
        cell.pack_start(renderer)

        self.check_text, cell = self._make_layout_style(group,
                                                        _("Check and text"),
                                                        size_group)
        renderer = gtk.CellRendererToggle()
        renderer.set_property('active', True)
        cell.pack_start(renderer, expand=False)
        renderer = gtk.CellRendererText()
        renderer.set_property('markup', 'Text')
        cell.pack_start(renderer)

        self.custom = gtk.RadioButton(group, _("Custom"))
        size_group.add_widget(self.custom)
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        hbox.pack_start(self.custom, False, False)
        custom_btn = gtk.Button(stock=gtk.STOCK_EDIT)
        custom_btn.set_sensitive(False)
        self.custom.set_sensitive(False)
        hbox.pack_start(custom_btn, True)
        self.vbox.pack_start(hbox, False, False)

        self.vbox.set_size_request(300, -1)

    def get_cell_renderers(self):
        """Returns a list of tuples. Each tuple has a type and a renderer"""
        renderers = []
        if self.text_only.get_active():
            renderers.append((str, gtk.CellRendererText()))
        elif self.image_text.get_active():
            renderers.append((gtk.gdk.Pixbuf, gtk.CellRendererPixbuf()))
            renderers.append((str, gtk.CellRendererText()))
        elif self.check_text.get_active():
            renderers.append((bool, gtk.CellRendererToggle()))
            renderers.append((str, gtk.CellRendererText()))
        else:
            print('custom layout not supported yet')

        return renderers

class CreateCellsDialog(CellsDialogMixin, BaseDialog):
    """Dialog to create the cell layout of a Column"""
    def __init__(self, parent=None):
        BaseDialog.__init__(self, parent, title=_('New layout'),
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OK, gtk.RESPONSE_OK))
        self._create_widgets()

        sep = gtk.HSeparator()
        self.vbox.pack_start(sep, False, False)

        label = gtk.Label(_('Title') + ':')
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        hbox.pack_start(label, False, False)

        self.title_entry = gtk.Entry()

        hbox.pack_start(self.title_entry, True, True)
        self.vbox.pack_start(hbox, False, False)

        self.vbox.show_all()

    def get_title(self):
        return self.title_entry.get_text()

    def set_title(self, title):
        self.title_entry.set_text(title)

class EditCellsDialog(CellsDialogMixin, PropertyEditorDialog):
    def _create_widgets(self):
        CellsDialogMixin._create_widgets(self)
        self.text_only.connect('toggled', self._on_button_toggled)
        self.image_text.connect('toggled', self._on_button_toggled)
        self.check_text.connect('toggled', self._on_button_toggled)
        self.custom.connect('toggled', self._on_button_toggled)

    def set_gadget(self, gadget, proxy):
        super(EditCellsDialog, self).set_gadget(gadget, proxy)

        column = self.gadget.widget
        cell_types = list(map(gobject.type_name, column.get_cell_renderers()))
        cell_types.sort()

        if cell_types == ['GtkCellRendererText']:
            self.text_only.set_active(True)
        elif cell_types == ['GtkCellRendererPixbuf', 'GtkCellRendererText']:
            self.image_text.set_active(True)
        elif cell_types == ['GtkCellRendererText', 'GtkCellRendererToggle']:
            self.check_text.set_active(True)
        else:
            self.custom.set_active(True)

    def _on_button_toggled(self, button):
        # TODO: use the proxy and a custom command so the user can undo this
        parent = Gadget.from_widget(self.gadget.widget.get_parent())
        column = self.gadget.widget

        # remove model types for this column
        if parent:
            parent.adaptor.before_change_column_layout(parent, self.gadget)

        column = self.gadget.widget
        self.gadget.adaptor.create_layout(column, self.get_cell_renderers())

        # add model types for this column
        if parent:
            parent.adaptor.after_change_column_layout(parent, self.gadget)

def get_column_button(column):
    # hackish method borrowed from Kiwi
    widget = column.get_widget()
    while not isinstance(widget, gtk.Button) and widget is not None:
        widget = widget.get_parent()
    return widget

def get_column_parent(column):
    button = get_column_button(column)
    if button:
        return button.get_parent()

class CommandAddRemoveTreeViewColumn(FlipFlopCommandMixin, Command):
    """
    Command for adding and removing columns to a tree view.
    """

    def __init__(self, tree_view, column, project, add):
        """
        Initialize the command.

        @param tree_view: the tree_view the column is being added/removed from
        @type tree_view: gazpacho.gadget.Gadget
        @param column: the column that should be added or removed
        @type column: gazpacho.gadget.Gadget
        @param project: the project that the tree_view belongs to
        @type project: gazpacho.project.Project
        @param add: True if the column should be added
        @type add: bool
        """
        FlipFlopCommandMixin.__init__(self, add)

        if add:
            description = _("Add column to tree view '%s'") % tree_view.name
        else:
            description = _("Remove column '%s' from tree view '%s'") % \
                          (column.name, tree_view.name)

        Command.__init__(self, description)

        self._tree_view = tree_view
        self._column = column
        self._project = project

    def _execute_add(self):
        """
        Add the gadgets to the sizegroup. This might mean that the
        sizegroup will be added as well.
        """
        self._tree_view.adaptor.add_child(self._tree_view, self._column)
        self._project.add_widget(self._column.widget, True)
        self._column.select()

    _execute_state1 = _execute_add

    def _execute_remove(self):
        """
        Remove the gadgets from the sizegroup. This might cause the
        sizegroup to be removed as well.
        """
        self._tree_view.adaptor.remove_child(self._tree_view, self._column)
        self._project.remove_widget(self._column.widget)

    _execute_state2 = _execute_remove

class GazpachoTreeViewColumn(gtk.TreeViewColumn):
    """The purpose of this class is make Gazpacho believe a gtk.TreeViewColumn
    is-a gtk.Widget

    Explanation: in GTK+ a gtk.TreeViewColumn inherits from GObject, not from
    gtk.Widget and so Gazpacho does not know how to handle TreeViewColumns.
    From the user point of view a TreeViewColumn is a 'piece' of a TreeView,
    something like a part of the main widget. So he/she wants to be able to
    see it and manipulate it in Gazpacho.

    So what this class does is redirect/delegate all the widget's methods to
    the internal widget a gtk.TreeViewColumn has (e.g. the button). In order
    to get access to that widget we need to call gtk.TreeViewColumn.set_widget
    first and keep it synchronized when removing a column and adding
    it again (undo/redo)
    """
    def __init__(self):
        super(GazpachoTreeViewColumn, self).__init__()
        self.update_widget()
        self.name = None
        self.reset()

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def add_events(self, events):
        self.get_widget().add_events(events)

    def flags(self):
        return self.get_widget().flags()

    def is_ancestor(self, ancestor):
        return self.get_widget().is_ancestor(ancestor)

    def connect(self, name, handler, data=None):
        if name in ('clicked', 'destroy', 'notify'):
            super(GazpachoTreeViewColumn, self).connect(name, handler, data)

    def set_redraw_on_allocate(self, value):
        self.get_widget().set_redraw_on_allocate(value)

    def drag_source_set(self, *args):
        pass

    def drag_dest_set(self, *args):
        pass

    def _get_button(self):
        return get_column_button(self)

    def get_parent(self):
        return get_column_parent(self)

    parent = property(get_parent)

    def get_parent_window(self):
        return self.get_parent().window

    def get_toplevel(self):
        return self.get_widget().get_toplevel()

    def get_window(self):
        return self._get_button().window

    window = property(get_window)

    def get_allocation(self):
        return self._get_button().allocation

    allocation = property(get_allocation)

    def set_title(self, title):
        self.set_property('title', title)
        widget = self.get_widget()
        if widget is None:
            self.update_widget()
        else:
            widget.set_text(title)

    def get_title(self):
        return self.get_property('title')

    def update_widget(self):
        widget = self.get_widget()
        if widget is None:
            title = self.get_property('title')
            label = gtk.Label(title)
            self.set_widget(label)
            label.show()

    def copy(self, other):
        """Copy all properties from 'other' into self"""
        self.name = other.name
        self.set_title(other.get_property('title'))
        for pspec in gobject.list_properties(gtk.TreeViewColumn):
            if pspec.flags & gobject.PARAM_WRITABLE != 0:
                value = other.get_property(pspec.name)
                self.set_property(pspec.name, value)

    def hide(self):
        self.get_widget().hide()

    def show(self):
        self.get_widget().show()

    def show_all(self):
        self.get_widget().show_all()

    def reset(self):
        self.clear()
        self.cell_renderers = []
        self.types = {}
        self.attributes = {}
        self.names = {}

    def add_cell_renderer(self, renderer_type, renderer, **attrs):
        self.cell_renderers.append(renderer)
        self.types[renderer] = renderer_type
        self.attributes[renderer] = attrs
        name = '%s-renderer%d' % (self.name, len(self.cell_renderers))
        self.names[renderer] = name
        self.pack_start(renderer)
        if attrs:
            self.set_attributes(renderer, **attrs)

    def get_type_for_cell_renderer(self, renderer):
        return self.types[renderer]

    def get_name_for_cell_renderer(self, renderer):
        return self.names[renderer]

    def add_attribute(self, renderer, attribute, column):
        self.attributes[renderer][attribute] = column
        super(GazpachoTreeViewColumn, self).add_attribute(renderer, attribute,
                                                          column)

    def get_attribute(self, renderer, attribute):
        return self.attributes[renderer][attribute]

    def get_attributes(self, renderer):
        return self.attributes[renderer]

    def update_attributes(self, shift):
        for r in self.cell_renderers:
            for key, value in list(self.attributes[r].items()):
                self.attributes[r][key] = value + shift

class TreeViewColumnAdaptor(WidgetAdaptor):
    def create(self, context, interactive=True):
        return GazpachoTreeViewColumn()

    def post_create(self, context, column, interactive=True):
        if not interactive:
            return

        d = CreateCellsDialog(context.get_application_window())
        d.set_title(column.get_name())
        response = d.run()
        if response == gtk.RESPONSE_OK:
            column.set_title(d.get_title())
            self.create_layout(column, d.get_cell_renderers())
            d.destroy()
        else:
            d.destroy()
            raise CreationCancelled()

    def create_layout(self, column, cells):
        column.reset()
        for cell_type, cell_renderer in cells:
            attributes = cell_renderer.get_data('gazpacho::attributes') or {}
            column.add_cell_renderer(cell_type, cell_renderer, **attributes)

    def get_children(self, context, column):
        return column.get_cell_renderers()

    def load(self, context, column):
        # column is a gtk.TreeViewColumn and we transform it into a
        # GazpachoTreeViewColumn
        gazpacho_column = GazpachoTreeViewColumn()
        gazpacho_column.copy(column)

        # copy the renderers also
        func = renderer_expert.get_type_based_on_renderer
        renderers = column.get_cell_renderers()
        cells = [(func(gobject.type_name(r)), r) for r in renderers]
        self.create_layout(gazpacho_column, cells)

        # now we replace the pure column with the gazpacho column
        # the old column is not useful anymore so we can set a custom widget
        # just to get its parent. see GTK+ bug #342471
        column.set_widget(gtk.Label())
        tree_view = get_column_parent(column)

        # when pasting a column from the clipboard, it is not attached to a
        # tree view yet
        if tree_view:
            tree_view.remove_column(column)
            tree_view.append_column(gazpacho_column)

        gazpacho_column.update_widget()

        project = context.get_project()
        return Gadget.load(gazpacho_column, project)

class TitleProp(CustomProperty, StringType):
    def get(self):
        return self.object.get_title()

    def set(self, value):
        self.object.set_title(value)

prop_registry.override_simple('GtkTreeViewColumn::title', TitleProp)

class LayoutPropEditor(PropertyCustomEditorWithDialog):
    dialog_class = EditCellsDialog
    button_text = _('Edit Layout Definition...')

class LayoutAdaptor(TransparentProperty, StringType):
    """This represents a fake property to edit the layout of a Column.

    It does not store anything because this information is stored in cell
    renderers inside the column itself. It's just a way to put a button
    in the Gazpacho interface to call the UIPropEditor.
    """
    custom_editor = LayoutPropEditor

prop_registry.override_property('GtkTreeViewColumn::layout', LayoutAdaptor)
