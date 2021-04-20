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

import gobject
import gtk

from gazpacho.i18n import _
from gazpacho.propertyeditor import PropertyEditorDialog
from gazpacho.util import select_iter

def create_image_only_button(stock, size=gtk.ICON_SIZE_MENU):
    """Create a stock button with only image"""
    image = gtk.Image()
    image.set_from_stock(stock, size)
    button = gtk.Button()
    button.add(image)
    return button

def create_scrolled_window(child,
                           hpolicy=gtk.POLICY_AUTOMATIC,
                           vpolicy=gtk.POLICY_AUTOMATIC):
    """Helper function to avoid repetitive code"""
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.set_shadow_type(gtk.SHADOW_IN)
    scrolled_window.set_policy(hpolicy, vpolicy)
    scrolled_window.add(child)
    return scrolled_window

class RendererExpert(object):
    """This singletone knows everything you always wanted to know about cell
    renderers

    - It knows which renderers is best for a data type
    - It knows how to edit a cell used by a particular renderer
    - It knows the best column title based on the renderer that column uses
    - It knows

    Ask him whatever you need about cell renderers. He knows everything!
    """

    # for each type we have:
    #  - renderer that best represent that type
    #  - title for a tree view column
    #  - renderer that's best for editing a model attribute of that type
    #  - renderer attribute that should be connected to the model data
    knowledge = {
        str: (gtk.CellRendererText, 'string',
              gtk.CellRendererText, 'text'),
        bool: (gtk.CellRendererToggle, 'bool',
               gtk.CellRendererToggle, 'active'),
        int: (gtk.CellRendererText, 'float',
              gtk.CellRendererText, 'text'),
        float: (gtk.CellRendererText, 'float',
                gtk.CellRendererText, 'text'),
        gtk.gdk.Pixbuf: (gtk.CellRendererPixbuf, 'image',
                         gtk.CellRendererText, 'pixbuf'),
        }

    def get_renderer_for_type(self, t):
        """What's the best renderer for editing a column of type t?"""
        return self.knowledge[t][2]()

    def get_column_name_for_type(self, t):
        """What's the best column title for a column of type t?"""
        return self.knowledge[t][1]

    def get_type_based_on_renderer(self, r):
        """If we already have a renderer, what should be its best type?"""
        for t, data in list(self.knowledge.items()):
            if gobject.type_name(data[0]) == r:
                return t

    def get_attribute_for_model(self, t):
        """What attribute of the renderer should be set with the model data?"""
        return self.knowledge[t][3]

    def get_type_names(self):
        """Returns a list with all the possible type names we know about"""
        return [v[1] for v in list(self.knowledge.values())]

    def make_renderer_editable(self, t, renderer, model, column):
        "Make this renderer editable and save its interactions into the model"
        if t == bool:
            renderer.set_property('activatable', True)
            renderer.connect('toggled', self._on_cell_toggled, model, column)
        else:
            renderer.set_property('editable', True)
            renderer.connect('edited', self._on_cell_edited, model, column)

    def _on_cell_edited(self, cell, path, new_text, model, column):
        model[path][column] = new_text

    def _on_cell_toggled(self, cell, path, model, column):
        model[path][column] = not model[path][column]

renderer_expert = RendererExpert()

GAZPACHO_MODEL_QDATA = 'gazpacho::model'

class GazpachoModel(object):
    """Wrapper around a TreeModel"""
    # mapping from gtypes to python types. Used when loading a model
    gtypes2python = {
        gobject.TYPE_STRING: str,
        gobject.TYPE_BOOLEAN: bool,
        gobject.TYPE_INT: int,
        gobject.TYPE_FLOAT: float,
        }
    def __init__(self, name, model=None):
        self._name = name

        self._hierarchical = False

        if model is not None:
            # load the given model
            n = model.get_n_columns()
            gtypes = [model.get_column_type(i) for i in range(n)]
            self._types = []
            for t in gtypes:
                try:
                    self._types.append(self.gtypes2python[t])
                except KeyError:
                    self._types.append(t)

            self._types += [str]
            self._model = gtk.ListStore(*self._types)
            self._copy_models(model, self._model)
        else:
            # the initial type is a fake one just to make the TreeView
            # shows its header and hence, the '+' button
            self._model = gtk.ListStore(str)

            self._types = [str]

        self._model.set_data(GAZPACHO_MODEL_QDATA, self)

    #@classmethod
    def from_model(cls, widget):
        return widget.get_data(GAZPACHO_MODEL_QDATA)
    from_model = classmethod(from_model)

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def add_column(self, column_type):
        """Add the column to the model and returns its index"""
        self._types = self._types[:-1]
        preserve_columns = []
        if len(self._types) > 0:
            preserve_columns = list(range(len(self._types)))
        self._types.append(column_type)
        self._types += [str]

        self._update_model(preserve_columns)

        return len(self._types) - 2

    def remove_column(self, column_index):
        preserve_columns = list(range(len(self._types)))
        del self._types[column_index]
        del preserve_columns[column_index]

        self._update_model(preserve_columns, column_index)

    def add_columns_for_tree_view_column(self, column):
        for renderer in column.get_cell_renderers():
            t = column.get_type_for_cell_renderer(renderer)
            index = self.add_column(t)
            attribute = renderer_expert.get_attribute_for_model(t)

            column.add_attribute(renderer, attribute, index)

    def remove_columns_of_tree_view_column(self, column):
        count = 0
        for renderer in column.get_cell_renderers():
            t = column.get_type_for_cell_renderer(renderer)
            attribute = renderer_expert.get_attribute_for_model(t)

            index = column.get_attribute(renderer, attribute)

            self.remove_column(index - count)
            count += 1

    def insert_columns_of_tree_view_column(self, column, index):
        offset = index
        preserve_columns = list(range(len(self._types)))
        ignore_columns = []
        for renderer in column.get_cell_renderers():
            t = column.get_type_for_cell_renderer(renderer)
            self._types.insert(offset, t)

            attribute = renderer_expert.get_attribute_for_model(t)
            column.add_attribute(renderer, attribute, offset)

            ignore_columns.append(offset)
            offset += 1

        self._update_model(preserve_columns, -1, ignore_columns)

    def get_hierarchical(self):
        return self._hierarchical

    def set_hierarchical(self, value):
        self._hierarchical = value

    def get_model(self):
        return self._model

    def get_types(self):
        # the last one is fake
        return self._types[:-1]

    def get_type_name(self):
        return gobject.type_name(self._model)

    def get_column_type_names(self):
        """
        @returns: a list of type names
        """
        model = self._model
        return [gobject.type_name(model.get_column_type(i))
                    for i in range(model.get_n_columns() - 1)]

    # Private

    def _update_model(self, preserve_columns=tuple(), removed_column=-1,
                      ignore_columns=tuple()):
        if preserve_columns:
            data = self._backup_data(preserve_columns)

        if self._hierarchical:
            self._model = gtk.TreeStore(*self._types)
        else:
            self._model = gtk.ListStore(*self._types)

        if preserve_columns:
            self._restore_data(data, removed_column, ignore_columns)

        self._model.set_data(GAZPACHO_MODEL_QDATA, self)

    def _backup_data(self, columns):
        data = []
        for row in self._model:
            data.append({})
            for col in columns:
                data[-1][col] = row[col]
        return data

    def _restore_data(self, data, removed_column=-1, ignore_columns=tuple()):
        for d in data:
            iter = self._model.append()
            for col, value in list(d.items()):
                if col in ignore_columns:
                    col += len(ignore_columns)
                if removed_column != -1 and col > removed_column:
                    col -= 1
                self._model.set_value(iter, col, value)

    def _copy_models(self, src, dst):
        """Copy the data from src to dst"""
        dst.clear()
        for row in src:
            iter = dst.append()
            for i, value in enumerate(row):
                dst.set_value(iter, i, value)

class GazpachoModelManager(object):
    def __init__(self):
        self._models = {}

    def _create_new_model_name(self):
        name = None
        i = 0
        while True:
            i += 1
            name = "model%d" % i
            if not name in self._models:
                break

        return name

    def create_model(self):
        """Add a model to the list using a unique name"""
        name = self._create_new_model_name()
        model = self._models[name] = GazpachoModel(name)
        return model

    def get_model(self, name):
        return self._models[name]

    def get_models(self):
        return list(self._models.values())

    def load_model(self, model):
        self._models[model.name] = GazpachoModel(model.name, model)

    def remove_model(self, model):
        del self._models[model.get_name()]

    def add_model(self, model):
        # check if we have a model with the same name
        name = model.get_name()
        if name in list(self._models.keys()):
            # give the model a new name
            name = self._create_new_model_name()
            model.set_name(name)

        self._models[name] = model

(CUSTOM_MODEL_TYPE,
 CUSTOM_MODEL_INDEX,
 CUSTOM_MODEL_TYPE_NAME) = list(range(3))

class ModelEditorDialog(PropertyEditorDialog):

    def _create_widgets(self):
        title = gtk.Label()
        title.set_markup('<span size="larger" weight="bold">%s</span>' %
                         _('Model editor'))
        self.vbox.pack_start(title, False, False)

        self.tabs = gtk.Notebook()
        self.vbox.pack_start(self.tabs, True, True)

        data_tab = gtk.VBox()
        self._create_data_tab(data_tab)
        self.tabs.append_page(data_tab, gtk.Label(_('Data')))

        types_tab = gtk.VBox()
        self._create_types_tab(types_tab)
        self.tabs.append_page(types_tab, gtk.Label(_('Types')))

        self.vbox.set_size_request(360, 340)

    def _create_types_tab(self, tab):
        tab.set_border_width(6)
        tab.set_spacing(6)

        text = _('Create model from widget')
        self.create_from_widget_btn = gtk.RadioButton(None, text)

        self.create_from_widget_btn.connect('toggled',
                                            self._on_creation_type_toggled)
        hbox = gtk.HBox()
        hbox.set_spacing(6)

        hbox.pack_start(self.create_from_widget_btn, False, False)
        self.widget_combo = gtk.combo_box_new_text()
        hbox.pack_start(self.widget_combo)
        tab.pack_start(hbox, False, False)

        self.custom_model_btn = gtk.RadioButton(self.create_from_widget_btn,
                                                _('Custom model'))
        self.custom_model_btn.connect('toggled',
                                      self._on_creation_type_toggled)
        tab.pack_start(self.custom_model_btn, False, False)

        self.custom_model_align = gtk.Alignment(0, 0, 1, 1)
        self.custom_model_align.set_padding(0, 0, 48, 0)

        hbox = gtk.HBox()
        hbox.set_spacing(6)
        self.custom_model_store = gtk.ListStore(object, int, str)
        self.custom_model_view = gtk.TreeView(self.custom_model_store)
        renderer1 = gtk.CellRendererText()
        renderer1.set_property('xalign', 1) # right alignment
        col1 = gtk.TreeViewColumn(_('Index'), renderer1,
                                  text=CUSTOM_MODEL_INDEX)
        self.custom_model_view.append_column(col1)
        renderer2 = gtk.CellRendererText()
        col2 = gtk.TreeViewColumn(_('Type'), renderer2,
                                  text=CUSTOM_MODEL_TYPE_NAME)
        self.custom_model_view.append_column(col2)
        scrolled_window = create_scrolled_window(self.custom_model_view,
                                                 hpolicy=gtk.POLICY_NEVER)
        hbox.pack_start(scrolled_window, True, True)

        table = gtk.Table(2, 2)
        self.types_combo = gtk.combo_box_new_text()
        for t in renderer_expert.get_type_names():
            self.types_combo.append_text(t)
        self.types_combo.set_active(0)
        self.add_type_btn = create_image_only_button(gtk.STOCK_ADD)
        self.del_type_btn = create_image_only_button(gtk.STOCK_REMOVE)

        table.attach(self.types_combo, 0, 1, 0, 1, yoptions=0)
        table.attach(self.add_type_btn, 1, 2, 0, 1, yoptions=0)
        table.attach(self.del_type_btn, 1, 2, 1, 2, yoptions=0)
        hbox.pack_start(table, False, False)

        self.custom_model_align.add(hbox)
        self.custom_model_align.set_sensitive(False)
        tab.pack_start(self.custom_model_align, True, True)

    def _create_data_tab(self, tab):
        tab.set_border_width(6)
        tab.set_spacing(6)

        self.tree_store_check = gtk.CheckButton(_('Allow hierarchical data'))
        self.tree_store_check.set_sensitive(False)
        tab.pack_start(self.tree_store_check, False, False)

        self.data_view = gtk.TreeView()
        selection = self.data_view.get_selection()
        selection.connect('changed', self._on_data_view_selection_changed)
        scrolled_window = create_scrolled_window(self.data_view)
        tab.pack_start(scrolled_window, True, True)

        hbox = gtk.HBox()
        table = gtk.Table(2, 3)
        self.add_row_btn = create_image_only_button(gtk.STOCK_ADD)
        self.add_row_btn.connect('clicked', self._on_add_row)
        table.attach(self.add_row_btn, 0, 1, 0, 1, xoptions=0, yoptions=0)
        self.del_row_btn = create_image_only_button(gtk.STOCK_REMOVE)
        self.del_row_btn.connect('clicked', self._on_del_row)
        table.attach(self.del_row_btn, 0, 1, 1, 2, xoptions=0, yoptions=0)
        self.up_row_btn = create_image_only_button(gtk.STOCK_GO_UP)
        self.up_row_btn.connect('clicked', self._on_up_row)
        table.attach(self.up_row_btn, 1, 2, 0, 1, xoptions=0, yoptions=0)
        self.down_row_btn = create_image_only_button(gtk.STOCK_GO_DOWN)
        self.down_row_btn.connect('clicked', self._on_down_row)
        table.attach(self.down_row_btn, 1, 2, 1, 2, xoptions=0, yoptions=0)
        self.left_row_btn = create_image_only_button(gtk.STOCK_GO_FORWARD)
        self.left_row_btn.connect('clicked', self._on_left_row)
        table.attach(self.left_row_btn, 2, 3, 0, 1, xoptions=0, yoptions=0)
        self.right_row_btn = create_image_only_button(gtk.STOCK_GO_BACK)
        self.right_row_btn.connect('clicked', self._on_right_row)
        table.attach(self.right_row_btn, 2, 3, 1, 2, xoptions=0, yoptions=0)

        hbox.pack_start(table, False, False)

        label = gtk.Label(_('Click on a cell to edit its contents'))
        hbox.pack_start(label, True, True)

        tab.pack_start(hbox, False, False)

    def _fill_widget_combo(self, project):
        """Fill the widget combo with the names of all the widgets in this
        project that can have a model"""
        self.widget_combo.get_model().clear()
        model_widgets = (gtk.TreeView, gtk.ComboBox, gtk.ComboBoxEntry)
        widgets = [w for w in project.get_widgets()
                      if isinstance(w, model_widgets)]
        for widget in widgets:
            self.widget_combo.append_text(widget.name)

    def _select_widget_in_widget_combo(self, widget_name):
        """Select the widget_name item in the widget_combo"""
        model = self.widget_combo.get_model()
        for i, row in enumerate(model):
            if row[0] == widget_name:
                self.widget_combo.set_active(i)
                break

    def _synchronize_types_view(self):
        """Fill the custom model with the information of the current model

        This way, if the user chooses 'custom model' he/she does not need to
        start from scratch
        """
        self.custom_model_store.clear()
        for col, t in enumerate(self.model.get_types()):
            name = renderer_expert.get_column_name_for_type(t)
            self.custom_model_store.append((t, col, name))

    def _synchronize_data_view(self):
        """Sync our data treeview with the model we are editing:

        - Put one tree column for each model column
        - Set the model of the treeview to this model
        """
        # clear previous columns
        col = self.data_view.get_column(0)
        while col is not None:
            self.data_view.remove_column(col)
            col = self.data_view.get_column(0)

        # set the new model
        self.data_view.set_model(self.model.get_model())

        # create the columns
        for col, t in enumerate(self.model.get_types()):
            renderer = renderer_expert.get_renderer_for_type(t)
            name = renderer_expert.get_column_name_for_type(t)
            attribute = renderer_expert.get_attribute_for_model(t)
            map = {attribute: col}
            column = gtk.TreeViewColumn(name, renderer, **map)
            self.data_view.append_column(column)

            # make the renderer editable
            renderer_expert.make_renderer_editable(t, renderer,
                                                   self.model.get_model(), col)

    def set_gadget(self, gadget, proxy):
        super(ModelEditorDialog, self).set_gadget(gadget, proxy)

        model = self.gadget.widget.get_model()
        if model:
            # Get the gazpacho model associated to this gadget
            gzmodel = GazpachoModel.from_model(model)
        else:
            # Or create a new one default one if it doesn't exist
            gzmodel = gadget.project.model_manager.create_model()
        self.model = gzmodel

        # setup the types tab
        self._fill_widget_combo(self.gadget.project)
        self._select_widget_in_widget_combo(self.gadget.name)
        self._synchronize_types_view()

        # do we have hierarchical data?
        self.tree_store_check.set_active(self.model.get_hierarchical())

        # prepare the treeview for data edition
        self._synchronize_data_view()

        # enable or disable buttons depending on the state
        self._update_data_buttons(self.data_view.get_selection())

    # Callbacks here:
    def _on_creation_type_toggled(self, btn):
        self.widget_combo.set_sensitive(
            self.create_from_widget_btn.get_active())

        self.custom_model_align.set_sensitive(
            self.custom_model_btn.get_active())

    def _on_data_view_selection_changed(self, selection):
        self._update_data_buttons(selection)

    def _on_add_row(self, btn):
        model = self.model.get_model()
        iter = model.append(None)
        # make the new row editable
        select_iter(self.data_view, iter)
        path = model.get_path(iter)
        column = self.data_view.get_column(0)
        self.data_view.set_cursor(path, column, True)

    def _on_del_row(self, btn):
        model, iter = self.data_view.get_selection().get_selected()
        if iter:
            model.remove(iter)

    def _on_up_row(self, btn):
        self._move_row(-1, self.model.get_model().move_before)

    def _on_down_row(self, btn):
        self._move_row(1, self.model.get_model().move_after)

    def _on_left_row(self, btn):
        """TODO for hierarchical models"""

    def _on_right_row(self, btn):
        """TODO for hierarchical models"""

    # helpers and internal methods:
    def _update_data_buttons(self, selection):
        # first disable all buttons
        self._set_sensitive_all_data_buttons(False)
        cols = self.data_view.get_columns()
        if not cols:
            return

        # if we have one or more columns that means we can add data
        self.add_row_btn.set_sensitive(True)

        model, iter = selection.get_selected()
        if not iter:
            return

        # if there is a row selected we can delete it
        self.del_row_btn.set_sensitive(True)

        size = len(model)
        if size > 1:
            index = model.get_path(iter)[0]

            # up is available if this is not the first one
            if index != 0:
                self.up_row_btn.set_sensitive(True)

            # down is available if this is not the last one
            if index != (size - 1):
                self.down_row_btn.set_sensitive(True)

    def _set_sensitive_all_data_buttons(self, value):
        self.add_row_btn.set_sensitive(value)
        self.del_row_btn.set_sensitive(value)
        self.up_row_btn.set_sensitive(value)
        self.down_row_btn.set_sensitive(value)
        self.left_row_btn.set_sensitive(value)
        self.right_row_btn.set_sensitive(value)

    def _move_row(self, amount, move_function):
        selection = self.data_view.get_selection()
        model, iter = selection.get_selected()
        if iter:
            index = model.get_path(iter)[0]
            index += amount
            move_function(iter, model.get_iter((index,)))
            self._update_data_buttons(selection)
