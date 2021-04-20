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

from gazpacho.commandmanager import command_manager
from gazpacho.command import Command
from gazpacho.i18n import _
from gazpacho.properties import prop_registry, CustomProperty, \
     PropertyCustomEditor, TransparentProperty, StringType, ObjectType
from gazpacho.stockicons import StockIconList
from gazpacho.gadget import Gadget, load_gadget_from_widget
from gazpacho.widgets.base.base import ContainerAdaptor

def get_button_state(button):
    """Get the state of the button in the form of a tuple with the following
    fields:
      - stock_id: string with the stock_id or None if the button is not
        using a stock_id
      - notext: boolean that says if the button has only a stock icon or
        if it also has the stock label
      - label: string with the contents of the button text or None
      - image_path: string with the path of a custom file for the
        image or None
      - position: one of gtk.POS_* that specifies the position of the
        image with respect to the label
    """
    stock_id = label = image_path = position = None
    notext = False
    icon_size = gtk.ICON_SIZE_BUTTON

    use_stock = button.get_use_stock()
    child_name = None
    child = button.get_child()
    image_file_name = None
    if child:
        image_file_name = child.get_data('image-file-name')
        child_name = child.get_name()

    # it is a stock button
    if use_stock and not image_file_name:
        stock_id = button.get_label()

    # it only has a text label
    elif isinstance(child, gtk.Label):
        label = child.get_text()

    # it has an image without text. it can be stock icon or custom image
    elif isinstance(child, gtk.Image):
        if image_file_name:

            image_path = image_file_name
        else:
            stock_id = child.get_property('stock')
            if not stock_id:
                print('Unknown button image state, no stock, no filename')
        notext = True
        icon_size = child.get_property('icon-size')
    # it has custom image and text
    elif isinstance(child, gtk.Alignment):
        box = child.get_child()

        children = box.get_children()
        image_child = None
        text_child = None
        text_last = True
        for c in children:
            if isinstance(c, gtk.Image):
                image_child = c
                text_last = False
            elif isinstance(c, gtk.Label):
                text_child = c
                text_last = True

        if isinstance(box, gtk.HBox):
            if text_last:
                position = gtk.POS_LEFT
            else:
                position = gtk.POS_RIGHT
        else:
            if text_last:
                position = gtk.POS_TOP
            else:
                position = gtk.POS_BOTTOM

        if image_child:
            image_path = image_child.get_data('image-file-name')

        if text_child:
            label = text_child.get_text()
        else:
            notext = True

    return (stock_id, notext, label, image_path, position, icon_size,
            child_name)

# Command for the contents property:
class CommandSetButtonContents(Command):
    def __init__(self, gadget, stock_id=None, notext=False, label=None,
                 image_path=None, position=-1, icon_size=gtk.ICON_SIZE_BUTTON,
                 child_name=None):
        description = _('Setting button %s contents') % gadget.name
        Command.__init__(self, description)

        self.gadget = gadget
        self.stock_id = stock_id
        self.notext = notext
        self.label = label
        self.image_path = image_path
        self.position = position
        self.icon_size = icon_size
        self.child_name = child_name

    def execute(self):
        widget = self.gadget
        button = self.gadget.widget
        state = get_button_state(button)
        use_stock = widget.get_prop('use-stock')
        label = widget.get_prop('label')
        self._clear_button(button)

        if self.stock_id:
            # stock button

            if self.notext:
                image = gtk.Image()
                image.set_from_stock(self.stock_id, self.icon_size)
                image.show()
                button.add(image)
            else:
                use_stock.set(True)
                label.set(self.stock_id)

        else:
            # custom button. 3 cases:
            # 1) only text, 2) only image or 3) image and text
            if self.label and not self.image_path:
                # only text
                label.set(self.label)
            elif not self.label and self.image_path:
                # only image
                image = gtk.Image()
                image.set_from_file(self.image_path)
                image.set_data('image-file-name', self.image_path)
                image.show()
                button.add(image)
            elif self.label and self.image_path:
                # image and text
                align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
                if self.position in (gtk.POS_LEFT, gtk.POS_RIGHT):
                    box = gtk.HBox()
                else:
                    box = gtk.VBox()
                align.add(box)
                image = gtk.Image()
                image.set_from_file(self.image_path)
                image.set_data('image-file-name', self.image_path)
                label = gtk.Label(self.label)
                if '_' in self.label:
                    label.set_use_underline(True)

                if self.position in (gtk.POS_LEFT, gtk.POS_TOP):
                    box.pack_start(image)
                    box.pack_start(label)
                else:
                    box.pack_start(label)
                    box.pack_start(image)

                align.show_all()
                button.add(align)

        if button.child:
            project = self.gadget.project
            button.child.set_name('')
            load_gadget_from_widget(button, project)
            if not button.child.get_name():
                project.set_new_widget_name(button.child)
            project.add_hidden_widget(button.child)
            self.gadget.setup_widget(button)

        # save the state for undoing purposes
        (self.stock_id, self.notext, self.label,
         self.image_path, self.position, self.icon_size,
         self.child_name) = state

    def _clear_button(self, button):
        "Clear the button and set default values for its properties"
        button.set_use_stock(False)
        button.set_use_underline(False)
        button.set_label('')

        child = button.get_child()
        if child:
            button.remove(child)
            project = self.gadget.project
            project.remove_hidden_widget(child)

# Adaptors for Button
class ButtonContentsEditor(PropertyCustomEditor):

    wide_editor = True

    def __init__(self):
        self.loading = False
        self.gadget = None
        self.application_window = None
        self.input = self.create()

    def get_editor_widget(self):
        return self.input

    def _create_check_entry_button(self, table, row, check_text, button_text,
                                   entry_handler, check_handler,
                                   button_handler):
        check = gtk.CheckButton(check_text)
        table.attach(check, 0, 1, row, row + 1,
                     xoptions=gtk.FILL, yoptions=gtk.FILL)
        hbox = gtk.HBox()
        entry = gtk.Entry()
        entry.connect('changed', entry_handler)
        hbox.pack_start(entry)
        button = gtk.Button(button_text)
        button.connect('clicked', button_handler)
        hbox.pack_start(button, False, False)
        table.attach(hbox, 1, 2, row, row + 1, xoptions=gtk.EXPAND|gtk.FILL,
                     yoptions=gtk.EXPAND|gtk.FILL)
        check.connect('toggled', check_handler)
        return check, entry, button

    def _create_label(self, table):
        "Create the widgets needed to set the label of a button"
        c, e, b = self._create_check_entry_button(table, 0, _('Label:'), '...',
                                                  self._on_entry_label_changed,
                                                  self._on_check_label_toggled,
                                                  self._on_button_label_clicked)
        self.check_label, self.entry_label, self.button_label = c, e, b


    def _create_image(self, table):
        "Create the widgets needed to set the image of a button"
        c, e, b = self._create_check_entry_button(table, 1, _('Image:'), '...',
                                                  self._on_entry_image_changed,
                                                  self._on_check_image_toggled,
                                                  self._on_button_image_clicked)
        self.check_image, self.entry_image, self.button_image = c, e, b


    def _create_position(self, table):
        """Create the widgets needed to set the combo with the position
        of the image"""
        label = gtk.Label(('Image position:'))
        label.set_sensitive(False)
        table.attach(label, 0, 1, 2, 3, xoptions=gtk.FILL, yoptions=gtk.FILL)

        liststore = gtk.ListStore(str, int)
        liststore.append((_('Left'), gtk.POS_LEFT))
        liststore.append((_('Right'), gtk.POS_RIGHT))
        liststore.append((_('Top'), gtk.POS_TOP))
        liststore.append((_('Bottom'), gtk.POS_BOTTOM))
        combo = gtk.ComboBox(liststore)
        renderer = gtk.CellRendererText()
        combo.pack_start(renderer)
        combo.add_attribute(renderer, 'text', 0)

        combo.set_sensitive(False)
        table.attach(combo, 1, 2, 2, 3, xoptions=gtk.EXPAND|gtk.FILL,
                     yoptions=gtk.EXPAND|gtk.FILL)

        combo.connect('changed', self._on_combo_position_changed)
        self.combo_position = combo
        self.label_position = label

    def _create_stock_widgets(self):
        "Create the widgets needed to setup a stock button"
        alignment = gtk.Alignment(1.0, 0.0, 1.0, 1.0)
        alignment.set_padding(0, 12, 48, 0)
        vbox = gtk.VBox()

        self.stock = StockIconList()
        self.stock.connect('changed', self._on_stock_list_changed)
        self.stock.set_sensitive(True)
        vbox.pack_start(self.stock, False, False, padding=6)

        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, False)

        self.check_notext = gtk.CheckButton(_('No text'))
        self.check_notext.connect('toggled', self._on_check_notext_toggled)
        hbox.pack_start(self.check_notext, False, False)

        label = gtk.Label(_('Icon size:'))
        hbox.pack_start(label, False, False, 6)

        self.icon_size = gtk.ComboBox()
        self.icon_size.set_sensitive(False)
        self.icon_size.connect('changed', self._on_icon_size_changed)
        cell = gtk.CellRendererText()
        self.icon_size.pack_start(cell, True)
        self.icon_size.add_attribute(cell, 'text', 0)
        model = gtk.ListStore(str, object)
        self.icon_size.set_model(model)
        for enum in list(gtk.IconSize.__enum_values__.values()):
            if enum == gtk.ICON_SIZE_INVALID:
                continue
            iter = model.append([enum.value_nick.capitalize(), enum])
            if enum == gtk.ICON_SIZE_BUTTON:
                self.icon_size.set_active_iter(iter)
        hbox.pack_start(self.icon_size, False, False)

        alignment.add(vbox)
        return alignment

    def _create_custom_widgets(self):
        "Create the widgets needed to setup a custom button"
        alignment = gtk.Alignment(1.0, 0.0, 1.0, 1.0)
        alignment.set_padding(0, 12, 48, 0)
        table = gtk.Table(rows=3, columns=2)
        table.set_col_spacings(6)
        table.set_row_spacings(2)

        self._create_label(table)

        self._create_image(table)

        self._create_position(table)

        alignment.add(table)

        return alignment

    def create(self):
        "Create the whole editor with all the widgets inside"

        mainvbox = gtk.VBox()

        # widgets to setup a custom button
        self.radio_custom = gtk.RadioButton(None, _('Use custom button:'))
        mainvbox.pack_start(self.radio_custom, False, False)

        self.custom_widgets = self._create_custom_widgets()
        mainvbox.pack_start(self.custom_widgets, True, True)

        # widgets to setup a stock button
        self.radio_stock = gtk.RadioButton(self.radio_custom,
                                           _('Use stock button:'))
        self.radio_stock.connect('toggled', self._on_radio_toggled)
        mainvbox.pack_start(self.radio_stock, False, False)
        self.stock_widgets = self._create_stock_widgets()
        mainvbox.pack_start(self.stock_widgets, True, True)

        # use an extra alignment to add some padding to the top
        al = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        al.set_padding(12, 0, 0, 0)
        al.add(mainvbox)
        al.show_all()
        return al

    def _on_radio_toggled(self, button):
        if self.loading:
            return

        # this is emitted when the stock radio is toggled
        value = self.radio_stock.get_active()
        self.stock_widgets.set_sensitive(value)
        self.custom_widgets.set_sensitive(not value)

        if value:
            self.set_stock()
        else:
            self.set_custom()

    def _on_check_label_toggled(self, button):
        if self.loading:
            return

        value = self.check_label.get_active()
        self.entry_label.set_sensitive(value)
        self.button_label.set_sensitive(value)
        self._set_position_sensitive(value and self.check_image.get_active())

        self.set_custom()

    def _on_check_image_toggled(self, button):
        if self.loading:
            return

        value = self.check_image.get_active()
        self.entry_image.set_sensitive(value)
        self.button_image.set_sensitive(value)
        self._set_position_sensitive(value and self.check_label.get_active())

        self.set_custom()

    def _set_position_sensitive(self, value):
        self.label_position.set_sensitive(value)
        self.combo_position.set_sensitive(value)

    def _on_stock_list_changed(self, stocklist, stock_id):
        if not self.loading:
            self.set_stock()

    def _on_check_notext_toggled(self, button):
        if not self.loading:
            self.set_stock()

        self.icon_size.set_sensitive(button.get_active())

    def _on_icon_size_changed(self, combobox):
        if not self.loading:
            self.set_stock()

    def _on_entry_label_changed(self, entry):
        if not self.loading:
            self.set_custom()

    def _on_entry_image_changed(self, entry):
        if not self.loading:
            self.set_custom()

    def _on_button_label_clicked(self, button):
        pass

    def _on_button_image_clicked(self, button):
        dialog = gtk.FileChooserDialog(_('Open image ...'),
                                       self.application_window,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN,
                                        gtk.RESPONSE_OK))
        file_filter = gtk.FileFilter()
        file_filter.set_name("Images")
        file_filter.add_mime_type("image/png")
        file_filter.add_mime_type("image/jpeg")
        file_filter.add_mime_type("image/gif")
        file_filter.add_mime_type("image/x-xpixmap")
        file_filter.add_pattern("*.png")
        file_filter.add_pattern("*.jpg")
        file_filter.add_pattern("*.gif")
        file_filter.add_pattern("*.xpm")

        dialog.add_filter(file_filter)

        response = dialog.run()
        filename = dialog.get_filename()
        if response == gtk.RESPONSE_OK and filename:
            self.entry_image.set_text(filename)

        dialog.destroy()

    def _on_combo_position_changed(self, combo):
        if not self.loading:
            self.set_custom()

    def set_stock(self):
        if not self.gadget:
            return

        stock_id = self.stock.get_stock_id()
        notext = self.check_notext.get_active()
        model = self.icon_size.get_model()
        icon_size = model[self.icon_size.get_active_iter()][1]
        child_name = None
        if self.gadget.widget.child:
            child_name = self.gadget.widget.child.get_name()
        cmd = CommandSetButtonContents(self.gadget, stock_id=stock_id,
                                       notext=notext, icon_size=icon_size,
                                       child_name=child_name)
        command_manager.execute(cmd, self.gadget.project)

    def set_custom(self):
        if not self.gadget:
            return

        label = None
        if self.check_label.get_active():
            label = self.entry_label.get_text() or None

        image = None
        if self.check_image.get_active():
            image = self.entry_image.get_text() or None

        position = None
        ac_iter = self.combo_position.get_active_iter()
        if ac_iter:
            model = self.combo_position.get_model()
            position = model[ac_iter][1]

        child_name = None
        if self.gadget.widget.child:
            child_name = self.gadget.widget.child.get_name()

        cmd = CommandSetButtonContents(self.gadget, label=label,
                                       image_path=image, position=position,
                                       child_name=child_name)
        command_manager.execute(cmd, self.gadget.project)


    def _set_combo_active_position(self, pos):
        for row in self.combo_position.get_model():
            if row[1] == pos:
                self.combo_position.set_active_iter(row.iter)
                break

    def update(self, context, widget, proxy):
        self.gadget = Gadget.from_widget(widget)
        self.application_window = context.get_application_window()

        self.loading = True

        # default values for some widgets
        self.check_notext.set_active(False)
        self.check_label.set_active(True)
        self.entry_label.set_text("")
        self.check_image.set_active(False)
        self.entry_image.set_text("")
        self.combo_position.set_active(0)
        self.combo_position.set_sensitive(False)

        (stock_id, notext, label,
         image_path, position,
         icon_size, child_name) = get_button_state(widget)

        if stock_id:
            self.stock_widgets.set_sensitive(True)
            self.custom_widgets.set_sensitive(False)
            self.radio_stock.set_active(True)

            self.stock.set_stock_id(stock_id)
            self.check_notext.set_active(notext)
            for row in self.icon_size.get_model():
                if row[1] == icon_size:
                    self.icon_size.set_active_iter(row.iter)
                    break
            self.icon_size.set_sensitive(notext)
        else:
            self.stock_widgets.set_sensitive(False)
            self.custom_widgets.set_sensitive(True)
            self.radio_custom.set_active(True)

            self.check_label.set_active(True)
            self.entry_label.set_sensitive(True)
            self.button_label.set_sensitive(True)
            if label is not None:
                self.entry_label.set_text(label)

            if image_path is not None:
                self.check_image.set_active(True)
                self.entry_image.set_sensitive(True)
                self.entry_image.set_text(image_path)
            else:
                self.entry_image.set_sensitive(False)
                self.button_image.set_sensitive(False)

            if label and image_path:
                self.combo_position.set_sensitive(True)
                self._set_combo_active_position(position)
            else:
                self.combo_position.set_sensitive(False)

        if self.gadget.widget.child:
            self.gadget.widget.child.set_name(child_name)
        self.loading = False

class ButtonContentsAdaptor(TransparentProperty, StringType):
    """This adaptor allow the user the choose between a stock button and
    a custom button.

    A stock button is a button with a stock-icon. The text is optional
    A custom button allow the user to add a label, an image and the position
    of the image with respect to the label.
    """
    custom_editor = ButtonContentsEditor

    def get(self):
        return get_button_state(self.object)

    def save(self):
        return None

prop_registry.override_property('GtkButton::contents', ButtonContentsAdaptor)

class LabelAdaptor(CustomProperty, StringType):

    editable = False

    def is_translatable(self):
        # If a stock id is set, do not make it translatable,
        # because we don't want to translate stock-id labels!
        stock_id = get_button_state(self.object)[0]
        if stock_id:
            return False

        return True

    def save(self):
        (stock_id, notext,
         label, image_path) = get_button_state(self.object)[:4]
        if ((stock_id and notext)
            or (not label and image_path)
            or (label and image_path)):
            return
        else:
            return self.object.get_property('label')

prop_registry.override_simple('GtkButton::label', LabelAdaptor)

class ButtonAdaptor(ContainerAdaptor):
    def load(self, context, widget):
        # XXX: Copied from widget adaptor, there ought to be a
        #      better way of saying "I do not want to any load children"

        project = context.get_project()
        gadget = Gadget.load(widget, project)

        # if the widget is a toplevel we need to attach the accel groups
        # of the application
        if gadget.is_toplevel():
            gadget.setup_toplevel()

        return gadget

    def save(self, context, gadget):
        """Create Gadgets for the possible children of
        this widget so they are saved with the button"""
        gtk_button = gadget.widget

        (stock_id, notext, label,
         image_path) = get_button_state(gtk_button)[:4]

        child = gtk_button.get_child()
        project = context.get_project()

        if ((stock_id and notext)         # case 1: stock item without text
            or (not label and image_path) # case 2: only image
            or (label and image_path)):   # case 3: text and image

            # XXX: load_widget should also check so widget is not
            #      loaded twice
            if not Gadget.from_widget(child):
                name = child.get_data('gazpacho::object-id')
                if not name:
                    self._create_names_for_internal_widgets(child, project)
                else:
                    child.set_name(name)
                load_gadget_from_widget(child, project)
                project.add_hidden_widget(child)

            # case 4: stock item with text (nothing to do)

            # case 5: only text (nothing to do)

        # FIXME: Under some circumstances we end up with a GtkAlignment
        #        when we don't really need it.
        #        Find out when it's not needed and remove it

    def _create_names_for_internal_widgets(self, widget, project):
        project.set_new_widget_name(widget)

        if not isinstance(widget, gtk.Container):
            return

        for child in widget.get_children():
            self._create_names_for_internal_widgets(child, project)

    def fill_empty(self, context, widget):
        pass

    def post_create(self, context, button, interactive):
        button.set_label(button.get_name())

# GtkButton
prop_registry.override_simple('GtkButton::use-stock', editable=False)

# GtkCheckButton
prop_registry.override_simple('GtkCheckButton::draw-indicator', default=True)

# GtkRadioButton
class RadioGroupProp(CustomProperty, ObjectType):
    # We need to override get_default, since
    # the standard mechanism to get the initial value
    # is calling get_property, but ::group is not marked as readable
    editable = True

    def get_default(self, gobj):
        return

    def get(self):
        groups = self.object.get_group()
        if len(groups) <= 1:
            return None

        for group in groups:
            if group.get_active():
                return group

    def set(self, group):
        if not group in self.object.get_group():
            self.object.set_group(group)

    def save(self):
        value = self.get()
        if not value or value == self.object:
            return
        return value.get_name()

prop_registry.override_simple('GtkRadioButton::group', RadioGroupProp)
