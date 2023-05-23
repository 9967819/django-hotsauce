# Copyright (C) 2004,2005 by SICEm S.L. and Imendio AB
#               2005,2006 by Async Open Source
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
from kiwi.python import Settable
from kiwi.utils import gsignal, type_register
from kiwi.ui.dialogs import BaseDialog, open
from kiwi.ui.widgets.list import List, Column
from kiwi.ui.widgets.entry import ProxyEntry

from gazpacho.commandmanager import command_manager
from gazpacho.i18n import _
from gazpacho.properties import PropertyCustomEditor, UNICHAR_PROPERTIES, \
     prop_registry, UnsupportedProperty, CommandSetProperty, \
     CommandSetTranslatableProperty, PropertySetError
from gazpacho.signaleditor import SignalEditor
from gazpacho.stockicons import StockIconDialog

class IncompleteFunctions(Exception):
    pass

TABLE_ROW_SPACING = 2
TABLE_COLUMN_SPACING = 6

(EDITOR_INTEGER,
 EDITOR_FLOAT,
 EDITOR_DOUBLE) = list(range(3))

(FLAGS_COLUMN_SETTING,
 FLAGS_COLUMN_NAME,
 FLAGS_COLUMN_MASK) = list(range(3))

class EditorProperty:
    """ For every PropertyClass we have a EditorProperty that is basically
    an input (widget) for that PropertyClass. """

    wide_editor = False

    def __init__(self, property_class, app):
        # The class this property corresponds to
        self.property_class = property_class

        self._app = app
        self._project = app.get_current_project()

        # The widget that modifies this property, the widget can be a
        # GtkSpinButton, a GtkEntry, GtkMenu, etc. depending on the property
        # type.
        self.input = None

        # The loaded property
        self.property = None

        # If we're in the process of loading the property
        self.property_loading = False

        # We set this flag when we are loading a new Property into this
        # EditorProperty. This flag is used so that when we receive a "changed"
        # signal we know that nothing has really changed, we just loaded a new
        # gadget
        self.loading = False

        # the label to the left of the input
        label = gtk.Label("%s:" % property_class.label)
        label.set_alignment(1.0, 0.5)

        # we need to wrap the label in an event box to add tooltips
        eventbox = gtk.EventBox()
        eventbox.add(label)

        self.description = eventbox

    def __cmp__(self, other):
        return cmp(self.property_class.priority, other.property_class.priority)

    def load(self, widget):
        # Should be overridden
        return

    def external_set(self, value):
        """
        This is called when something external changes the property,
        Override this in a subclass and update the displayed content
        """

    # XXX: untested
    def set(self, value):
        try:
            cmd = CommandSetProperty(self.property, value)
            command_manager.execute(cmd, self._project)
        except PropertySetError:
	    # The value set by the user was not valid, so we
	    # have to restore it to the old value.
            self.external_set(self.property.value)

    def set_translatable_property(self, text, comment_text, translatable,
                                  has_context):
        cmd = CommandSetTranslatableProperty(
            self.property, text, comment_text, translatable, has_context)
        command_manager.execute(cmd, self._project)

    def _property_changed(self, prop):
        self.external_set(prop.get())

    def _start_load(self, widget):
        if self.property_class.child:
            prop = widget.get_child_prop(self.property_class.name)
        else:
            prop = widget.get_prop(self.property_class.name)
        prop.add_change_notify(self._property_changed)
        self.property = prop

        assert self.property
        self.property_loading = True

    def _finish_load(self):
        self.property_loading = False

    def _internal_load(self, value):
        """This is the virtual method that actually put the data in the editor
        widget.
        Most subclasses implements this (But not EditorPropertySpecial)
        """

class EditorPropertyNumeric(EditorProperty):

    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)
        self._value_changed_id = -1
        self._entry_changed_id = -1

    def load(self, widget):
        self._start_load(widget)
        self._internal_load(self.property.value)

        self.input.set_data('user_data', self)
        self._finish_load()

    def _internal_load(self, value):
        if self.property_class.name in UNICHAR_PROPERTIES:
            if isinstance(self.input, gtk.Editable):
                self.input.delete_text(0, -1)
                self.input.insert_text(value)
        #elif self.property_class.optional:
        #    button, spin = self.input.get_children()
        #    button.set_active(self.property.enabled)
        #    spin.set_sensitive(self.property.enabled)
        #    button.set_data('user_data', self)
        #    v = float(value)
        #    spin.set_value(v)
        elif value is not None:
            try:
                v = float(value)
            except ValueError:
                v = 0
            self.input.set_value(v)

    def _changed_unichar(self, entry):
        if self.property_loading:
            return

        # We need to handle the text as a unicode string. Note when
        # importing gtk the encoding will be forced to utf-8
        text = entry.get_chars(0, -1).decode()
        if text:
            self.set(text[0])

    def _create_input_unichar(self):
        entry = gtk.Entry()
        # it's to prevent spirious beeps ...
        entry.set_max_length(2)
        self._entry_changed_id = entry.connect('changed', self._changed_unichar)
        self.input = entry

    def _changed_numeric(self, spin):
        if self.property_loading:
            return

        numeric_type = spin.get_data('NumericType')
        if numeric_type == EDITOR_INTEGER:
            value = spin.get_value_as_int()
        elif numeric_type == EDITOR_FLOAT:
            value = spin.get_value()
        elif numeric_type == EDITOR_DOUBLE:
            value = spin.get_value()
        else:
            value = 0

        self.set(value)

    def _changed_enabled(self, check_button):
        if self.property_loading:
            return

        l = self.input.get_children()
        spin = l[1]
        state = check_button.get_active()
        spin.set_sensitive(state)
        prop = check_button.get_data('user_data')
        prop.property.enabled = state

    def _create_input_numeric(self, numeric_type):
        spin = gtk.SpinButton(self.property_class.get_adjustment(),
                              self.property_class.climb_rate,
                              self.property_class.digits)
        spin.set_data("NumericType", numeric_type)
        self._value_changed_id = spin.connect('value_changed', self._changed_numeric)

        # Some numeric types are optional, for example the default window size,
        # so they have a toggle button right next to the spin button
        #if self.property_class.optional:
        #    check = gtk.CheckButton()
        #    hbox = gtk.HBox()
        #    hbox.pack_start(check, False, False)
        #    hbox.pack_start(spin)
        #    check.connect('toggled', self._changed_enabled)
        #    self.input = hbox
        #else:
        self.input = spin

    def external_set(self, value):
        widget = self.input
        if isinstance(widget, gtk.SpinButton):
            widget.handler_block(self._value_changed_id)
            widget.set_value(value)
            widget.handler_unblock(self._value_changed_id)
        elif isinstance(self.input, gtk.Entry):
            widget.handler_block(self._entry_changed_id)
            widget.set_text(value)
            widget.handler_unblock(self._entry_changed_id)

class EditorPropertyInteger(EditorPropertyNumeric):
    def __init__(self, property_class, app):
        EditorPropertyNumeric.__init__(self, property_class, app)

        if self.property_class.name in UNICHAR_PROPERTIES:
            self._create_input_unichar()
        else:
            self._create_input_numeric(EDITOR_INTEGER)

class EditorPropertyFloat(EditorPropertyNumeric):
    def __init__(self, property_class, app):
        EditorPropertyNumeric.__init__(self, property_class, app)
        self._create_input_numeric(EDITOR_FLOAT)

class EditorPropertyDouble(EditorPropertyNumeric):
    def __init__(self, property_class, app):
        EditorPropertyNumeric.__init__(self, property_class, app)
        self._create_input_numeric(EDITOR_DOUBLE)

class EditorPropertyText(EditorProperty):
    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)

        self.input = gtk.HBox()
        # If the current data contains more than one line,
        # use a GtkTextView to display the data, otherwise just use a
        # normal GtkEntry
        if property_class.multiline:
            view = gtk.TextView()
            view.set_editable(True)
            text_buffer = view.get_buffer()
            text_buffer.connect('changed', self._on_text_buffer__changed)
            self.input.pack_start(view)
        else:
            self._entry = gtk.Entry()
            self._entry.connect('changed', self._on_entry__changed)
            self.input.pack_start(self._entry)

        if self.property_class.translatable:
            button = gtk.Button('...')
            button.connect('clicked', self._on_i18n_button__clicked)
            self.input.pack_start(button, False, False)

    def external_set(self, value):
        self.property_loading = True
        self._internal_load(value)
        self.property_loading = False

    def load(self, widget):
        self._start_load(widget)

        self._internal_load(self.property.value)

        self.input.set_data('user_data', self)

        self._finish_load()

    def _internal_load(self, value):
        # Text inputs are an entry or text view inside an hbox
        text_widget = self.input.get_children()[0]

        if isinstance(text_widget, gtk.Editable):
            pos = text_widget.get_position()
            text_widget.delete_text(0, -1)
            if value:
                text_widget.insert_text(value)

            text_widget.set_position(pos)

        elif isinstance(text_widget, gtk.TextView):
            text_buffer = text_widget.get_buffer()
            text_buffer.set_text(value)
        else:
            print ('Invalid Text Widget type')

    # Callbacks

    def _on_i18n_button__clicked(self, button):
        self._show_i18n_dialog()

    def _on_entry__changed(self, entry):
        if self.property_loading:
            return

        text = entry.get_chars(0, -1)
        self.set(text)

    def _on_text_buffer__changed(self, text_buffer):
        if self.property_loading:
            return

        start = text_buffer.get_iter_at_offset(0)
        end = text_buffer.get_iter_at_offset(text_buffer.get_char_count())
        text = text_buffer.get_text(start, end, False)
        self.set(text)

    # Private

    def _show_i18n_dialog(self):
        editor = self.input.get_toplevel()

        translatable = self.property.translatable
        has_context = self.property.has_i18n_context
        comment_text = self.property.i18n_comment

        dialog = BaseDialog(editor, _('Edit Text Property'),
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OK, gtk.RESPONSE_OK))

        dialog.set_has_separator(False)

        vbox = gtk.VBox(False, 6)
        vbox.set_border_width(8)
        vbox.show()

        dialog.vbox.pack_start(vbox, True, True, 0)

        # The text content
        label = gtk.Label()
        label.set_markup_with_mnemonic(_('_Text:'))
        label.show()
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 0)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        scrolled_window.set_size_request(400, 200)
        scrolled_window.show()

        vbox.pack_start(scrolled_window)

        text_view = gtk.TextView()
        text_view.show()
        label.set_mnemonic_widget(text_view)

        scrolled_window.add(text_view)

        text_buffer = text_view.get_buffer()

        text = self.property.value
        if text is not None:
            text_buffer.set_text(text)

        # Translatable and context prefix
        hbox = gtk.HBox(False, 12)
        hbox.show()

        vbox.pack_start(hbox, False, False, 0)

        translatable_button = gtk.CheckButton(_("T_ranslatable"))
        translatable_button.set_active(translatable)
        translatable_button.show()
        hbox.pack_start(translatable_button, False, False, 0)

        context_button = gtk.CheckButton(_("_Has context prefix"))
        context_button.set_active(has_context)
        context_button.show()
        hbox.pack_start(context_button, False, False, 0)

        # Comments
        label = gtk.Label()
        label.set_markup_with_mnemonic(_("Co_mments for translators:"))
        label.show()
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 0)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        scrolled_window.set_size_request(400, 200)
        scrolled_window.show()

        vbox.pack_start(scrolled_window)

        comment_view = gtk.TextView()
        comment_view.show()
        label.set_mnemonic_widget(comment_view)

        scrolled_window.add(comment_view)

        comment_buffer = comment_view.get_buffer()

        if comment_text is not None:
            comment_buffer.set_text(comment_text)

        res = dialog.run()
        if res == gtk.RESPONSE_OK:
            translatable = translatable_button.get_active()
            has_context = context_button.get_active()

            start, end = text_buffer.get_bounds()
            text = text_buffer.get_text(start, end, False)

            start, end = comment_buffer.get_bounds()
            comment_text = comment_buffer.get_text(start, end, False)

            self.set_translatable_property(text, comment_text, translatable,
                                           has_context)

            # Update the entry in the property editor
            #self.load(self.property.widget)

        dialog.destroy()

class EditorPropertyTextBrowse(EditorPropertyText):
    """
    EditorPropertyTextBrowse is an editor which behaves like a text entry, but
    it has an extra button on the right side which you can click so it opens up
    a file chooser dialog.
    To customize the types that can be loaded, override the get_filter() method
    """
    def __init__(self, property_class, app):
        EditorPropertyText.__init__(self, property_class, app)

        if property_class.translatable:
            raise TypeError(
                "You can't use a EditorPropertyTextBrowse on a translatable property")

        button = gtk.Button('...')
        button.connect('clicked', self._on_browse_button__clicked)
        self.input.pack_start(button, False, False)

    def _on_browse_button__clicked(self, button):
        self._show_browse_dialog()

    def _show_browse_dialog(self):
        filename = open("Select an image", parent=self.input.get_toplevel(),
                        filter=self.get_filter())
        if filename:
            self._entry.set_text(filename)

    def get_filter(self):
        """
        @returns: a gtk.FileFilter or None
        """

class EditorPropertyImage(EditorPropertyTextBrowse):
    """
    A property editor for loading images
    """
    def get_filter(self):
        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_mime_type("image/x-xpixmap")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.gif")
        filter.add_pattern("*.xpm")
        return filter

class EditorPropertyStock(EditorPropertyText):
    """
    A property editor for stock icons
    """
    def __init__(self, property_class, app):
        EditorPropertyText.__init__(self, property_class, app)

        button = gtk.Button('...')
        button.connect('clicked', self._on_browse_button__clicked)
        self.input.pack_start(button, False, False)

    def _on_browse_button__clicked(self, button):
        self._show_stock_icon_dialog()

    def _show_stock_icon_dialog(self):
        dialog = StockIconDialog(parent=self.input.get_toplevel())
        dialog.select(self.property.value)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            stock_id = dialog.get_selected()
            self._entry.set_text(stock_id)
        dialog.hide()

class EditorPropertyEnum(EditorProperty):
    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)

        model = gtk.ListStore(str, object)
        for name, value in self.property_class.get_choices():
            model.append((name, value))

        combo_box = gtk.ComboBox(model)
        renderer = gtk.CellRendererText()
        combo_box.pack_start(renderer)
        combo_box.set_attributes(renderer, text=0)
        combo_box.connect('changed', self._changed_enum)

        self.input = combo_box

    def load(self, widget):
        self._start_load(widget)
        self._internal_load(self.property.value)
        self._finish_load()

    def _internal_load(self, value):
        idx = 0
        for choice in self.property.get_choices():
            if choice[1] == value:
                break
            idx += 1
        self.input.set_active(idx)

    def _changed_enum(self, combo_box):
        if self.property_loading:
            return

        active_iter = combo_box.get_active_iter()
        model = combo_box.get_model()
        value = model[active_iter][1]
        self.set(value)

class EditorPropertyFlags(EditorProperty):
    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)

        self.input = List([Column('value', data_type=bool, editable=True),
                           Column('name', data_type=str),
                           Column('mask', data_type=str, visible=False)])
        self.input.get_treeview().set_headers_visible(False)
        self.input.connect('cell-edited', self._on_input__cell_edited)

        # Populate the model with the flags
        self.input.add_list(
            [Settable(value=False, name=name, mask=mask)
             for name, mask in property_class.get_choices()])
        self.input.show()

    def load(self, widget):
        self._start_load(widget)
        self._internal_load(self.property.value)
        self._finish_load()

    def _internal_load(self, value):
        for flag in self.input:
            flag.value = bool((value & flag.mask) == flag.mask)
            self.input.update(flag)

    # Called when the value column is edited, since it's the only
    # editable column.
    def _on_input__cell_edited(self, flags, flag, attribute):
        value = 0
        for flag in self.input:
            if flag.value:
                value |= flag.mask

        if value != self.property.value:
            self.set(value)

class EditorPropertyBoolean(EditorProperty):
    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)

        button = gtk.ToggleButton(_('No'))
        self._toggled_id = button.connect('toggled', self._changed_boolean)

        self.input = button

    def external_set(self, value):
        self.input.handler_block(self._toggled_id)
        self.input.set_active(value)
        self.input.handler_unblock(self._toggled_id)

    def load(self, widget):
        self._start_load(widget)
        self._internal_load(self.property.value)

        self.input.set_data('user_data', self)
        self._finish_load()

    def _internal_load(self, state):
        label = self.input.get_child()

        if state:
            value = 'yes'
        else:
            value = 'no'
        label.set_text(value)

        self.input.set_active(state)

    def _changed_boolean(self, button):
        if self.property_loading:
            return

        if button.get_active():
            value = 'yes'
        else:
            value = 'no'

        label = button.get_child()
        label.set_text(value)
        self.set(button.get_active())

class EditorPropertyCustomEditor(EditorProperty):
    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)

        self.custom_editor = self.property_class.custom_editor()
        self.input = self.custom_editor.get_editor_widget()

    def load(self, gadget):
        self._start_load(gadget)

        self.widget = gadget

        proxy = EditorValueProxy()
        proxy.connect('value-set', self._value_changed, gadget)
        proxy.connect('property-set', self._property_set, gadget)

        context = gadget.project.context
        self.custom_editor.update(context, gadget.widget, proxy)
        self._finish_load()

    def _value_changed(self, proxy, value, gadget):
        if self.property_loading:
            return

        self.set(value)

    def _property_set(self, proxy, prop_id, value, gadget):
        if self.property_class.child:
            property = gadget.get_child_prop(prop_id)
        else:
            property = gadget.get_prop(prop_id)

        if not property or self.property_loading:
            return

        self.set(value)

class EditorValueProxy(gobject.GObject):
    gsignal('value-set', object)
    gsignal('property-set', str, object)

    def set_value(self, value):
        self.emit('value-set', value)

    def set_property(self, prop, value):
        self.emit('property-set', prop, value)

if gtk.pygtk_version < (2, 8):
    gobject.type_register(EditorValueProxy)

# BUGS:
#   the cellrenderers show up twice
#   no way to remove the widget, eg set it to empty
#
class EditorPropertyObject(EditorProperty):
    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)

        self.property_class = property_class
        self.property_type = property_class.type
        self.project = app.get_current_project()

        self.model = gtk.ListStore(str, object)

        combo_box = gtk.ComboBox(self.model)
        renderer = gtk.CellRendererText()
        combo_box.pack_start(renderer)
        combo_box.set_attributes(renderer, text=0)
        combo_box.connect('changed', self._changed_enum)

        self.input = combo_box

    def load(self, widget):
        self._start_load(widget)
        current = self.property.get()

        self.model.clear()
        for pwidget in self.project.get_widgets():
            if isinstance(pwidget, gtk.Window):
                continue

            if not gobject.type_is_a(pwidget, self.property_type):
                continue

            iter = self.model.append((pwidget.name, pwidget))
            if pwidget == current:
                self.input.set_active_iter(iter)

        self._finish_load()

    def _changed_enum(self, combo_box):
        if self.property_loading:
            return

        active_iter = combo_box.get_active_iter()
        model = combo_box.get_model()
        widget = model[active_iter][1]
        self.set(widget)

class PropertyEditorDialog(BaseDialog):
    """This is a base abstract class for those editors that need to be
    opened in a dialog.
    """

    def __init__(self):
        """The widgets of the dialog are created in the virtual method
        _create_widgets.
        """
        BaseDialog.__init__(self,
                            buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.widget = None
        self.gadget = None
        self.proxy = None

        # avoid destrcution when clicking the x button
        self.connect('delete-event', self._on_delete_event)
        self.connect('response', self._on_response)

        self.set_resizable(False)

        self._create_widgets()

        self.vbox.show_all()

    def _create_widgets(self):
        """Subclasses should override this."""

    def set_gadget(self, gadget, proxy):
        """Every time the user clicks on a custom property editor button
        we are called with a different widget and proxy.
        """
        self.proxy = proxy
        self.gadget = gadget

    def _on_delete_event(self, dialog, event):
        self.hide()
        return True

    def _on_response(self, dialog, response_id):
        self.hide()

class PropertyCustomEditorWithDialog(PropertyCustomEditor):
    """A custom editor which is just a button that opens up a dialog"""

    # subclasses should probably want to override the dialog_class
    dialog_class = PropertyEditorDialog
    button_text = _('Edit...')

    def __init__(self):
        self.dialog = self.dialog_class()
        self.input = gtk.Button(self.button_text)
        self.input.connect('clicked', self.on_button_clicked)

        self.application_window = None
        self.proxy = None
        self.edited_gadget = None

    def get_editor_widget(self):
        return self.input

    def update(self, context, widget, proxy):
        from gazpacho.gadget import Gadget

        self.application_window = context.get_application_window()
        self.edited_gadget = Gadget.from_widget(widget)
        self.proxy = proxy

    def on_button_clicked(self, button):
        self.dialog.set_transient_for(self.application_window)
        self.dialog.set_gadget(self.edited_gadget, self.proxy)
        self.dialog.present()

class EditorPropertyName(EditorProperty):

    duplicate_name_msg = _("There is already a widget with this name")
    no_name_msg = _("The widget must have a name")

    def __init__(self, property_class, app):
        EditorProperty.__init__(self, property_class, app)

        self.input = ProxyEntry()
        self.input.set_property('data-type', str)
        self.input.connect('changed', self._changed_text)

    def load(self, widget):
        self._start_load(widget)
        self._internal_load(widget)
        self._finish_load()

    def _internal_load(self, widget):
        value = self.property.value
        pos = self.input.get_position()
        self.input.delete_text(0, -1)
        if value:
            self.input.insert_text(value)

        self.input.set_position(pos)

        # validate that the name exists and is unique
        if not value:
            self.input.set_invalid(self.no_name_msg)
        elif self._project.get_gadget_by_name(value) != widget:
            self.input.set_invalid(self.duplicate_name_msg)
        else:
            self.input.set_valid()

    def _changed_text(self, entry):
        """
        Update the name property of the widget if the name is valid.
        """
        if self.property_loading:
            return

        name = entry.get_chars(0, -1)
        if not name:
            self.input.set_invalid(self.no_name_msg)
        elif self._project.get_gadget_by_name(name):
            self.input.set_invalid(self.duplicate_name_msg)
        else:
            self.input.set_valid()
            self.set(name)


# this maps property types with EditorProperty classes
property_map = {
    gobject.TYPE_INT: EditorPropertyInteger,
    gobject.TYPE_UINT: EditorPropertyInteger,
    gobject.TYPE_FLOAT: EditorPropertyFloat,
    gobject.TYPE_DOUBLE: EditorPropertyDouble,
    gobject.TYPE_ENUM: EditorPropertyEnum,
    gobject.TYPE_FLAGS: EditorPropertyFlags,
    gobject.TYPE_BOOLEAN: EditorPropertyBoolean,
    gobject.TYPE_STRING: EditorPropertyText
    }

class EditorPage(gtk.Table):
    """
    For each widget type that we have modified, we create an EditorPage.
    An EditorPage is a gtk.Table subclass with all the widgets to edit
    a particular widget type
    """
    def __init__(self):
        gtk.Table.__init__(self, 1, 1, False)

        self._tooltips = gtk.Tooltips()
        self._rows = 0

        self.set_border_width(6)
        self.set_row_spacings(TABLE_ROW_SPACING)
        self.set_col_spacings(TABLE_COLUMN_SPACING)

    def _attach_row(self, label, editable):
        row = self._rows
        if label:
            self.attach(label, 0, 1, row, row+1,
                        xoptions=gtk.FILL, yoptions=gtk.FILL)
            self.attach(editable, 1, 2, row, row+1,
                        xoptions=gtk.EXPAND|gtk.FILL,
                        yoptions=gtk.EXPAND|gtk.FILL)
        else:
            self.attach(editable, 0, 2, row, row+1)
        self._rows += 1

    def append_item(self, editor):
        if editor.input:
            self._tooltips.set_tip(editor.description,
                                   editor.property_class.description)
            # TODO: Hmm.
            if editor.property_class.custom_editor.wide_editor:
                # no label for this editor since it need both columns
                # of the table
                description = None
            else:
                description = editor.description

        self._attach_row(description, editor.input)

    def append_name_field(self, widget_adaptor):
        # Class
        label = gtk.Label(_('Class')+':')
        label.set_alignment(1.0, 0.5)
        class_label = gtk.Label(widget_adaptor.editor_name)
        class_label.set_alignment(0.0, 0.5)
        self._attach_row(label, class_label)

    def reset(self):
        list(map(self.remove, self.get_children()))
        self._rows = 0

class PropertyEditor(gtk.Notebook):
    gsignal('add-signal', str, int, int, str)

    def __init__(self, app):
        gtk.Notebook.__init__(self)
        self.set_size_request(350, 300)

        self._app = app

        # The editor has (at this moment) four tabs this are pointers to the
        # vboxes inside each tab.
        self._vbox_gadget = self._notebook_page(_('Widget'))
        self._vbox_packing = self._notebook_page(_('Packing'))
        self._vbox_common = self._notebook_page(_('Common'))
        self._vbox_signals = self._notebook_page(_('Signals'))

        # Create the pages, one for widget properties and
        # one for the common ones
        self._widget_table = EditorPage()
        self._vbox_gadget.pack_start(self._widget_table, False)

        self._common_table = EditorPage()
        self._vbox_common.pack_start(self._common_table, False)

        self._packing_table = EditorPage()
        self._vbox_packing.pack_start(self._packing_table, False)

        # A handy reference to the widget that is loaded in the editor. None
        # if no widgets are selected
        self._loaded_gadget = None

        # A list of properties for the current widget
        # XXX: We might want to cache this
        self._widget_properties = []
        self._widget_editors = {}

        self._signal_editor = None

    def _notebook_page(self, name):
        vbox = gtk.VBox()

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(vbox)
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)

        self.insert_page(scrolled_window, gtk.Label(name), -1)

        return vbox

    def do_add_signal(self, id_widget, type_widget, id_signal, callback_name):
        pass

    def _create_editor_property(self, property_class):
        if property_class.custom_editor != PropertyCustomEditor:
            return EditorPropertyCustomEditor(property_class, self._app)

        if property_class.editor:
            return property_class.editor(property_class, self._app)

        # Special case GObject subclasses
        if gobject.type_is_a(property_class.type, gobject.GObject):
            return EditorPropertyObject(property_class, self._app)

        if property_class.base_type in property_map:
            return property_map[property_class.base_type](property_class,
                                                          self._app)

    def _create_property_pages(self, gadget, adaptor):
        widget_table = self._widget_table
        common_table = self._common_table
        packing_table = self._packing_table
        parent = gadget.widget.get_parent()
        widget_table.reset()
        common_table.reset()
        packing_table.reset()

        widget_table.append_name_field(adaptor)

        # Put the property widgets on the right page
        widget_properties = []


        editors = self._widget_editors.get((adaptor.type_name, parent))
        if editors is None:
            # Append name to the widget table first
            widget_editors = self._widget_editors.setdefault(
                (adaptor.type_name, parent), [])

            if isinstance(gadget.widget, gtk.Widget):
                property_class = prop_registry.get_prop_type('GtkWidget',
                                                             'name')
                editor = EditorPropertyName(property_class, self._app)
                widget_editors.append((widget_table, editor))

            for property_class in prop_registry.list(adaptor.type_name,
                                                     parent):
                if not property_class.editable:
                    continue

                # Skip name, it's already added above
                name = property_class.name
                if name == 'name':
                    continue

                # Check the property too, sort of a hack
                if (name in gadget.properties and
                    not gadget.properties[name].editable):
                    continue

                if property_class.child:
                    page = packing_table
                elif property_class.owner_type in (gtk.Object.__gtype__,
                                                   gtk.Widget.__gtype__):
                    page = common_table
                else:
                    page = widget_table

                try:
                    editor = self._create_editor_property(property_class)
                    if not editor:
                        continue
                except UnsupportedProperty:
                    continue

                widget_editors.append((page, editor))

            editors = self._widget_editors.get((adaptor.type_name, parent))

        editors.sort()

        for page, editor in editors:
            page.append_item(editor)
            widget_properties.append(editor)

        self._widget_properties = widget_properties

        # XXX: Remove this, show all widgets individually instead
        widget_table.show_all()
        common_table.show_all()
        packing_table.show_all()

    def _create_signal_page(self):
        if self._signal_editor:
            return self._signal_editor

        self._signal_editor = SignalEditor(self, self._app)
        self._vbox_signals.pack_start(self._signal_editor)

    def _get_parent_types(self, widget):
        retval = [type(widget)]
        while True:
            parent = widget.get_parent()
            if not parent:
                return retval
            retval.append(type(parent))
            widget = parent

    def _needs_rebuild(self, gadget):
        """
        Return True if we need to rebuild the current property pages, False
        if it's not require.
        """

        if not self._loaded_gadget:
            return True

        # Check if we need to rebuild the interface, otherwise we might end
        # up with a (child) properties which does not belong to us
        # FIXME: This implementation is not optimal, in some cases it'll
        # rebuild even when it doesn't need to, a better way would be
        # to compare child properties.
        if (self._get_parent_types(self._loaded_gadget.widget) !=
            self._get_parent_types(gadget.widget)):
            return True

        return False

    def _load_gadget(self, gadget):
        if self._needs_rebuild(gadget):
            self._create_property_pages(gadget, gadget.adaptor)
            self._create_signal_page()

        for widget_property in self._widget_properties:
            widget_property.load(gadget)
        self._signal_editor.load_gadget(gadget)

        self._loaded_gadget = gadget

    def hide_content(self):
        self._set_visible(False)

    def _set_visible(self, value):
        for vbox in (self._vbox_gadget,
                     self._vbox_common,
                     self._vbox_packing):
            if value:
                vbox.show()
            else:
                vbox.hide()

    def display(self, gadget):
        "Display a widget in the editor"

        self._set_visible(True)

        # Skip widget if it's already loaded or None
        if self._loaded_gadget == gadget or not gadget:
            return

        self._load_gadget(gadget)

    def refresh(self, prop_name=None):
        """Reread properties and update the editor

        If prop_name is given only refresh that property editor
        """
        if not self._loaded_gadget:
            return

        if prop_name:
            for widget_property in self._widget_properties:
                if widget_property.property_class.name == prop_name:
                    widget_property.load(self._loaded_gadget)
        else:
            self._load_gadget(self._loaded_gadget)

    def get_loaded_gadget(self):
        return self._loaded_gadget

type_register(PropertyEditor)

