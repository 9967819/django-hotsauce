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
import gobject
import gtk
from kiwi.environ import environ
from kiwi.utils import gsignal

from gazpacho.catalog import get_all_catalogs, get_custom_ui_filename, CustomUI
from gazpacho.dndhandlers import DND_PALETTE_TARGET, INFO_TYPE_PALETTE
from gazpacho.i18n import _

class Palette(gtk.VBox):
    gsignal('toggled')

    def __init__(self):
        """Create a palette widget for a list of catalogs.

        A Palette widget graphically represents a set of widget groups
        as described in catalog files and allows for the notification
        of selection changes and the currently selected element.

        A Palette has the following elements: a selector, a button group and
        a notebook.

        The selector allows to toggle between "select widget" mode and
        "add widget" mode.

        The button group has a radio button for each group in the catalogs,
        which additionally activates the group's own notebook page.

        The notebook has a page for each existing catalog group. These
        pages show a row per widget and each row holds an icon and a label
        to represent the widget element. This data is taken from the catalog.

        Derived classes connect to the Palette's "toggled" signal
        to be notified of selection changes so they may read the
        "current" property holding the selected "widget_adaptor" and react
        accordingly.
        """
        gtk.VBox.__init__(self)

        # The WidgetAdaptor corresponding to the selected button. None if
        # the selector button is pressed.
        self._current = None

        self.pack_start(self._selector_new(), False)
        self.pack_start(gtk.HSeparator(), False, padding=3)

        #The vbox that contains the titles of the sections in buttons
        self._groups_vbox = gtk.VBox()
        self.pack_start(self._groups_vbox, False)
        self.pack_start(gtk.HSeparator(), False, padding=3)

        #  Where we store the different catalogs
        self._notebook = gtk.Notebook()
        self._notebook.set_show_tabs(False)
        self._notebook.set_show_border(False)
        self.pack_end(self._notebook)

        # The number of sections in this palette
        self._nb_sections = 0

        self._tooltips = gtk.Tooltips()

        # Each section in the palette has a radio button. This is the
        # button group to which new section buttons must be appended
        self._sections_button_group = None

        catalogs = get_all_catalogs()
        custom_ui_filename = get_custom_ui_filename()
        if custom_ui_filename:
            custom_ui = CustomUI(custom_ui_filename)
            for group in custom_ui.widget_groups:
                self.append_widget_group(group)
        else:
            for catalog in catalogs:
                for group in catalog.widget_groups:
                    self.append_widget_group(group)

        # persistent mode means that a widget keep selected after
        # creating an instance of it. It is activated when the
        # user holds SHIFT while selecting the widget
        self.persistent_mode = False

    # some needed property accesors for the currently selected element
    def get_current(self):
        return self._current

    def set_current(self, value):
        self._current = value
    current = property(get_current, set_current)

    def _selector_new(self):
        """Return a new selector.

        The selector is a button used to switch between "widget selection"
        and "widget add" mode. This makes the cursor look change. When no
        widget is selected in the notebook then the selector button is pressed.
        """
        hbox = gtk.HBox()
        # The selector is part of the widgets_button_group, so that when
        # no widget is selected, its button is pressed.
        self._selector = gtk.RadioButton(None)
        self._selector.set_name('Selector')
        self._selector.set_mode(False)
        self._selector.set_relief(gtk.RELIEF_NONE)

        # Each widget in a section has a button in the palette. This is the
        # button group, since only one may be pressed.
        self._widgets_button_group = self._selector.get_group()

        image = gtk.Image()
        image.set_from_file(environ.find_resource('pixmap', 'selector.png'))
        self._selector.add(image)
        self._selector.connect('toggled', self._on_button_toggled)

        # A label which contains the name of the class currently selected or
        # "Selector" if no widget class is selected
        self._label = gtk.Label(_('Selector'))
        self._label.set_alignment(0.0, 0.5)

        hbox.pack_start(self._selector, False, False)
        hbox.pack_start(self._label, padding=2)
        hbox.show_all()

        return hbox

    def _on_button_toggled(self, button):
        """Show the selected button label by the selector and make it current.

        Derived classes use the toggled signal to get notified of changes and
        read the "current" property to get the widget_adaptor.
        """
        if not button.get_active():
            return

        self.persistent_mode = False

        if button == self._selector:
            self._current = None
            self._label.set_text(_('Selector'))
        else:
            modifiers = button.window.get_pointer()[2]
            if modifiers & gtk.gdk.CONTROL_MASK:
                self.persistent_mode = True

            self._current = button.get_data('user')
            self._label.set_text(self._current.editor_name)

        self.emit('toggled')

    def _on_catalog_button_toggled(self, button):
        "Show notebook page associated to a catalog button"
        page = button.get_data('page')
        self._notebook.set_current_page(page)
        return True

    def do_toggled(self):
        pass

    def append_widget_group(self, group):
        """Append a new group of widgets to the palette.

        For the given catalog group a new RadioButton is added to control
        the display of the notebook page that holds the widget table. This
        table is also built from this method.
        """
        page = self._nb_sections
        self._nb_sections += 1

        # add the button to the existing group or create a new group
        # to be used from now on.
        if not self._sections_button_group:
            button = gtk.RadioButton(None, group.title)
        else:
            button = gtk.RadioButton(self._sections_button_group,
                                     group.title)
	# FIXME: This needs to be able to handle space, ampersand etc.
        button.set_name(group.name.replace('-', '_'))
        # use 1st button in the group as reference for the group
        # and store the notebook page controlled by the button
        self._sections_button_group = button.get_group()[0]
        button.set_mode(False)
        button.set_data('page', page)
        button.connect('toggled', self._on_catalog_button_toggled)

        self._groups_vbox.pack_start(button, False)

        # add the selection
        self._notebook.append_page(self._widget_table_create(group),
                                   gtk.Label(''))
        self._notebook.show()

    def _setup_dnd(self, widget):
        targets = [DND_PALETTE_TARGET]
        widget.drag_source_set(gtk.gdk.BUTTON1_MASK, targets,
                               gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        widget.connect('drag_begin', self._dnd_drag_begin_cb)
        widget.connect('drag_data_get', self._dnd_drag_data_get_cb)

    def _widget_table_create(self, group):
        """Return a table with an icon and a label for every widget in a group.

        Each button stores with it a 'user' attribute that holds the
        widget_adaptor denomination from the catalog data.
        """

        vbox = gtk.VBox()
        for widget_adaptor in group:
            if not widget_adaptor.palette_name:
                continue

            radio = gtk.RadioButton(self._widgets_button_group[0])
            radio.set_name(widget_adaptor.generic_name)
            radio.connect('toggled', self._on_button_toggled)
            radio.set_data('user', widget_adaptor)
            radio.set_mode(False)
            radio.set_relief(gtk.RELIEF_NONE)

            # Drag and Drop, but only for non-toplevel widgets
            if not widget_adaptor.is_toplevel():
                self._setup_dnd(radio)
            vbox.pack_start(radio, False, False)

            if widget_adaptor.tooltip:
                self._tooltips.set_tip(radio, widget_adaptor.tooltip)

            hbox = gtk.HBox(spacing=2)
            hbox.pack_start(widget_adaptor.icon, False, False)
            radio.add(hbox)

            label = gtk.Label(widget_adaptor.palette_name)
            label.set_alignment(0.0, 0.5)
            hbox.pack_start(label, padding=1)

            self._widgets_button_group = radio.get_group()

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(vbox)
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)

        return scrolled_window

    def _dnd_drag_begin_cb(self, source_gadget, drag_context):
        """Callback for handling the 'drag_begin' event. It will just
        set a nice looking drag icon."""

        source_gadget.clicked()

        adaptor = source_gadget.get_data('user')

        if adaptor:
            source_gadget.drag_source_set_icon_pixbuf(adaptor.pixbuf)

    def _dnd_drag_data_get_cb(self, source_gadget, context,
                              selection_data, info, time):
        adaptor = source_gadget.get_data('user')

        if adaptor and info == INFO_TYPE_PALETTE:
            selection_data.set(selection_data.target, 8, adaptor.type_name)
            return

        selection_data.set(selection_data.target, 8, "")

    def unselect_widget(self):
        "Leave \"add widget\" mode and back to the \"select widget\" mode."
        self._selector.set_active(True)

    def select_widget(self, catalog, widgetname):
        """Select a widget in the palette from a catalog with name widgetname.

        This selection triggers the clicked signal for the widget button
        in the palette.
        """
        # select the catalog
        pagenum = -1
        for button in self._groups_vbox.get_children():
            if button.get_label() == catalog:
                pagenum = button.get_data('page')
                break

        if pagenum == -1:
            return

        vbox = self._notebook.get_nth_page(pagenum).get_child().get_child()
        # then select the widget
        for button in vbox.get_children():
            wc = button.get_data('user')
            if wc.name == widgetname:
                button.clicked()

gobject.type_register(Palette)

if environ.epydoc:
    palette = object()
else:
    palette = Palette()
