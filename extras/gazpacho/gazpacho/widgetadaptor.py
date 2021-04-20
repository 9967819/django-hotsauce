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

import os

import gobject
import gtk
from kiwi.environ import environ

from gazpacho import util
from gazpacho.cursor import Cursor
from gazpacho.interfaces import BaseWidgetAdaptor
from gazpacho.gadget import Gadget, load_gadget_from_widget

class CreationCancelled(Exception):
    """This is raised when the user cancels the creation of a widget"""
    pass

def create_pixbuf(generic_name, palette_name, library_name, resource_path):
    pixbuf = None

    if generic_name and palette_name:
        filename = '%s.png' % generic_name
        if resource_path is not None:
            path = environ.find_resource('resource',
                                         os.path.join(library_name, filename))
        else:
            path = environ.find_resource('pixmap', filename)

        if path is not None:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            except gobject.GError:
                pass

    # If we cannot find the icon and it's going to be shown in the palette
    # Print a warning and create an icon of a missing image instead
    if not pixbuf and palette_name:
        print('Warning: Icon for %s is missing' % palette_name)
        da = gtk.DrawingArea()
        pixbuf = da.render_icon(gtk.STOCK_MISSING_IMAGE,
                                gtk.ICON_SIZE_MENU)
    return pixbuf

def create_icon(pixbuf):
    image = gtk.Image()
    image.set_from_pixbuf(pixbuf)
    return image

class WidgetAdaptor(object, BaseWidgetAdaptor):
    """Base class for all widget adaptors

    A widget adaptor is the main class of a library plugin. There is a widget
    adaptor for every widget in the library that needs to do anything special
    upon certain events in Gazpacho. See this class virtual methods for
    examples of such special events.

    The rest of widgets (e.g. regular widgets) use just an instance of this
    base class, which provides the basic functionality.

    Check gazpacho/widgets/base/base.py for examples of widget adaptors.

    @ivar type: GTK type for this widget. Used to create widgets with
                gobject.new()
    @ivar type_name: type_name is used when saving the xml
    @ivar editor_name: Name displayed in the editor
    @ivar name: Optional identifier of adaptor, GType name of type will
                be used if not specified
    @ivar generic_name: generic_name is used to create default widget names
    @ivar palette_name: palette_name is used in the palette
    @ivar tooltip: the tooltip is shown in the palette
    @ivar library:
    @ivar icon:
    @ivar cursor:
    @ivar pixbuf
    @ivar default: default widget as created in gobject.new(). It is used to
                   decide if any property has changed
    @ivar default_child: for packing properties we need to save the
                         default child too
    """

    type = None
    name = None

    def __init__(self, type_name, generic_name, palette_name, library,
                 resource_path, tooltip):
        """
        @param type_name:
        @param generic_name:
        @param palette_name:
        @param library:
        @param resource:
        @param tooltip:
        """
        self._default = None
        self._default_child = {}
        #self.type = None
        #self.name = None
        if self.type:
            if not issubclass(self.type, gtk.Widget):
                raise TypeError("%s.type needs to be a gtk.Widget subclass")
            type_name = gobject.type_name(self.type)
        else:
            try:
                self.type = gobject.type_from_name(type_name)
            except RuntimeError:
                raise AttributeError(
                    "There is no registered widget called %s" % type_name)
        self.type_name = type_name

        self.editor_name = type_name
        self.generic_name = generic_name
        self.palette_name = palette_name
        self.library = library
        self.tooltip = tooltip
        self.pixbuf = create_pixbuf(generic_name, palette_name, library.name,
                                    resource_path)
        self.icon = create_icon(self.pixbuf)
        self.cursor = Cursor.create(self.pixbuf)

    # Virtual methods

    def create(self, context, interactive=True):
        """
        Called when creating a widget, it should return an instance
        of self.type
        """
        return self.library.create_widget(self.type)

    def post_create(self, context, widget, interactive=True):
        """
        Called after all initialization is done in the creation process.

        It takes care of creating the gadgets associated with internal
        children. It's also the place to set sane defaults, e.g. set the size
        of a window.
        """

    def fill_empty(self, context, widget):
        """
        After the widget is created this function is called to put one or
        more placeholders in it. Only useful for container widgets
        """

    def replace_child(self, context, old_widget, new_widget, parent_widget):
        """
        Called when the user clicks on a placeholder having a palette icon
        selected. It replaced a placeholder for the new widget.

        It's also called in the reverse direction (replacing a widget for a
        placeholder) when removing a widget or undoing a create operation.
        """

    def save(self, context, widget):
        """
        Prepares the widget to be saved. Basically this mean setting all
        the gazpacho.widgets for internal children so the filewriter can
        iterate through them and write them correctly.
        """

    def load(self, context, widget):
        """
        Build a gadget from a widget

        The loading is a two step process: first we get the widget tree from
        gazpacho.loader or libglade and then we create the gadgets
        from that widget tree. This function is responsable of
        the second step of this loading process
        """
        from gazpacho.placeholder import Placeholder
        project = context.get_project()
        gadget = Gadget.load(widget, project)

        # create the children
        if isinstance(widget, gtk.Container):
            for child in util.get_all_children(widget):
                if isinstance(child, Placeholder):
                    continue
                load_gadget_from_widget(child, project)

        # if the widget is a toplevel we need to attach the accel groups
        # of the application
        if gadget.is_toplevel():
            gadget.setup_toplevel()

        return gadget

    def button_release(self, context, widget, event):
        """
        Called when a button release event occurs in the widget.

        Note that if the widget is a windowless widget the event is actually
        produced in its first parent with a gdk window so you will probably
        want to translate the event coordinates.
        """
        return False # keep events propagating the usual way

    def motion_notify(self, context, widget, event):
        """
        Called when the mouse is moved on the widget.

        Note that if the widget is a windowless widget the event is actually
        produced in its first parent with a gdk window so you will probably
        want to translate the event coordinates.
        """
        return False # keep events propagating the usual way

    def get_children(self, context, widget):
        """
        To get the list of children for a widget, overridable by subclasses
        """
        return []

    def delete(self, context, widget):
        """
        Called when a widget has been deleted.
        """
        pass

    def restore(self, context, widget, data):
        """
        Called when a widget that were previously deleted has been
        restored again.
        """
        pass

    # Public API

    def get_default(self):
        return self._default

    def get_default_prop_value(self, prop, parent_type):
        """
        This is responsible for accessing the default value of a property.
        And what we consider default is the value assigned to an
        object immediatelly after it's called gobject.new.
        parent_name is used for packing properties
        @param prop: a property
        @param parent_type: parent gtype
        """
        if not prop.child:
            if not self._default:
                self._default = self.library.create_widget(self.type)

            default_value = prop.get_default(self._default)
        else:
            # Child properties are trickier, since we do not only
            # Need to create the object, but the parent too
            if not parent_type in self._default_child:
                parent = gobject.new(parent_type)
                child = gobject.new(self.type_name)
                self._default_child[parent_type] = parent, child
                parent.add(child)
            else:
                parent, child = self._default_child[parent_type]

            default_value = parent.child_get(child, prop.name)[0]

        return default_value

    def list_signals(self):
        """
        @returns: a list of signals
        """
        signals = []

        gobject_gtype = gobject.GObject.__gtype__
        gtype = self.type
        while True:
            kn = gobject.type_name(gtype)
            signal_names = list(gobject.signal_list_names(gtype))
            signal_names.sort()
            signals += [(name, kn) for name in signal_names]
            if gtype == gobject_gtype:
                break

            gtype = gobject.type_parent(gtype)

        return signals

    def is_toplevel(self):
        """
        @returns: True if it's a toplevel, False otherwise
        """
        return gobject.type_is_a(self.type, gtk.Window)
