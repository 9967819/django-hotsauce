# Copyright (C) 2005 by Async Open Source
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

import pango
import gtk
from kiwi.utils import PropertyObject, gproperty

from gazpacho.properties import prop_registry
from gazpacho.loader.custom import WidgetAdapter as LoaderAdapter, \
     adapter_registry
from gazpacho.widgets.base.base import WidgetAdaptor

custom_xpm = [
    "8 8 2 1",
    "  c #d6d6d6",
    "o c #bbbbbb",
    "        ",
    " oooooo ",
    " o    o ",
    " o    o ",
    " o    o ",
    " o    o ",
    " oooooo ",
    "        ",
    ]

MIN_WIDTH = MIN_HEIGHT = 20

# GObject
class Custom(PropertyObject, gtk.DrawingArea):
    gproperty('int1', int, nick='Integer 1', default=-1, minimum=-1)
    gproperty('int2', int, nick='Integer 2', default=-1, minimum=-1)
    gproperty('string1', str, nick='String 1')
    gproperty('string2', str, nick='String 2')
    gproperty('creation-function', str, nick='Creation function')
    gproperty('last-modification-time', str)

    def __init__(self, name=None, **kwargs):
        gtk.DrawingArea.__init__(self)
        PropertyObject.__init__(self, **kwargs)
        self.connect('notify::string1', lambda self, *a: self.queue_draw())

        if name:
            self.set_name(name)

        self._layout = self.create_pango_layout("")
        self._layout.set_font_description(
            pango.FontDescription("sans serif 12"))
        self._pixmap = None

        self.set_flags(self.flags() | gtk.CAN_FOCUS)

    def prop_set_visible(self, v):
        # Evil evil bug in PropertyObject, needs to
        # be investigated closer.
        self.set_property('visible', v)
        return v

    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)

        events = (gtk.gdk.EXPOSURE_MASK |
                  gtk.gdk.BUTTON_PRESS_MASK |
                  gtk.gdk.POINTER_MOTION_MASK)

        colormap = self.get_colormap()
        self.window = gtk.gdk.Window(self.get_parent_window(),
                                     x=self.allocation.x,
                                     y=self.allocation.y,
                                     width=self.allocation.width,
                                     height=self.allocation.height,
                                     window_type=gtk.gdk.WINDOW_CHILD,
                                     wclass=gtk.gdk.INPUT_OUTPUT,
                                     visual=self.get_visual(),
                                     colormap=colormap,
                                     event_mask=self.get_events() | events)

        self.window.set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)

        if not self._pixmap:
            pixmap, _ = gtk.gdk.pixmap_colormap_create_from_xpm_d(
                None, colormap, None, custom_xpm)

            self._pixmap = pixmap

        self.window.set_back_pixmap(self._pixmap, False)

    def do_size_allocate(self, allocation):
        self.allocation = allocation
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

    def do_size_request(self, requisition):
        requisition.width = MIN_WIDTH
        requisition.height = MIN_HEIGHT

    def do_expose_event(self, event):
        light_gc = self.style.light_gc[gtk.STATE_NORMAL]
        dark_gc = self.style.dark_gc[gtk.STATE_NORMAL]
        w, h = event.window.get_size()

        # These lines make the Placeholder look like a button
        event.window.draw_line(light_gc, 0, 0, w - 1, 0)
        event.window.draw_line(light_gc, 0, 0, 0, h - 1)
        event.window.draw_line(dark_gc, 0, h -1, w - 1, h - 1)
        event.window.draw_line(dark_gc, w - 1, 0, w - 1, h - 1)

        text = "Custom"
        if self.string1:
            text += ": %s" % self.string1
        self._layout.set_text(text)

        fontw, fonth = self._layout.get_pixel_size()
        self.style.paint_layout(self.window, self.state, False,
                                event.area, self, "label",
                                (w - fontw) / 2,
                                (h - fonth) / 2,
                                self._layout)
        return False

# Adapter
class CustomAdaptor(WidgetAdaptor):
    type = Custom
    name = 'Custom'

# Loader
class CustomLoaderAdapter(LoaderAdapter):
    object_type = Custom
    def construct(self, name, gtype, properties):
        return Custom()
adapter_registry.register_adapter(CustomLoaderAdapter)

CUSTOM_TYPE = 'gazpacho+widgets+base+custom+Custom'
prop_registry.override_simple(CUSTOM_TYPE + '::int1',
                              translatable=False, minimum=-1)
prop_registry.override_simple(CUSTOM_TYPE + '::int2',
                              translatable=False, minimum=-1)
prop_registry.override_simple(CUSTOM_TYPE + '::string1',
                              translatable=False)
prop_registry.override_simple(CUSTOM_TYPE + '::string2',
                              translatable=False)
prop_registry.override_simple(CUSTOM_TYPE + '::creation-function',
                              translatable=False)
prop_registry.override_simple(CUSTOM_TYPE + '::last-modification-time',
                              translatable=False, editable=False)
