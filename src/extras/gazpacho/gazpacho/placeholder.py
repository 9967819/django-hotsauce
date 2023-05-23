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
from kiwi.component import get_utility

from gazpacho import gapi
from gazpacho.annotator import draw_annotations
from gazpacho.commandmanager import command_manager
from gazpacho.cursor import Cursor
from gazpacho.interfaces import IGazpachoApp
from gazpacho.popup import PlaceholderPopup
from gazpacho.util import get_parent

placeholder_xpm = [
    # columns rows colors chars-per-pixel
    "8 8 2 1",
    "  c #bbbbbb",
    ". c #d6d6d6",
    # pixels
    " .  .   ",
    ".    .  ",
    "      ..",
    "      ..",
    ".    .  ",
    " .  .   ",
    "  ..    ",
    "  ..    ",
    ]

MIN_WIDTH = MIN_HEIGHT = 20

class Placeholder(gtk.Widget):
    def __init__(self):
        gtk.Widget.__init__(self)

        self._xpm_data = placeholder_xpm
        self._pixmap = None

        self.set_flags(self.flags() | gtk.CAN_FOCUS)

        from gazpacho.dndhandlers import PlaceholderDnDHandler
        dndhandler = PlaceholderDnDHandler()
        dndhandler.connect_drop_handlers(self)

        self.show()

    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)

        events = (gtk.gdk.EXPOSURE_MASK |
                  gtk.gdk.BUTTON_PRESS_MASK |
                  gtk.gdk.POINTER_MOTION_MASK)

        self.window = gtk.gdk.Window(self.get_parent_window(),
                                     x=self.allocation.x,
                                     y=self.allocation.y,
                                     width=self.allocation.width,
                                     height=self.allocation.height,
                                     window_type=gtk.gdk.WINDOW_CHILD,
                                     wclass=gtk.gdk.INPUT_OUTPUT,
                                     visual=self.get_visual(),
                                     colormap=self.get_colormap(),
                                     event_mask=self.get_events() | events)

        self.window.set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)

        if not self._pixmap:
            t = gtk.gdk.pixmap_colormap_create_from_xpm_d(None,
                                                          self.get_colormap(),
                                                          None,
                                                          self._xpm_data)
            self._pixmap = t[0] # t[1] is the transparent color

        self.window.set_back_pixmap(self._pixmap, False)

    def get_project(self):
        """Get the project to which this placeholder belong."""
        project = None
        parent = get_parent(self)
        if parent:
            project = parent.project
        return project

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

        # These lines make the Placeholder looks like a button
        event.window.draw_line(light_gc, 0, 0, w - 1, 0)
        event.window.draw_line(light_gc, 0, 0, 0, h - 1)
        event.window.draw_line(dark_gc, 0, h -1, w - 1, h - 1)
        event.window.draw_line(dark_gc, w - 1, 0, w - 1, h - 1)

        draw_annotations(self, event.window)

        return False

    def do_motion_notify_event(self, event):
        Cursor.set_for_widget_adaptor(event.window,
                                      get_utility(IGazpachoApp).add_class)

        return False

    def do_button_press_event(self, event):
        if not self.flags() & gtk.HAS_FOCUS:
            self.grab_focus()

        if event.button == 1 and event.type == gtk.gdk.BUTTON_PRESS:
            app = get_utility(IGazpachoApp)
            # A widget type is selected in the palette.
            # Add a new widget of that type
            if app.add_class:
                gapi.create_gadget(app.get_current_project(), app.add_class,
                                   self)

            # Shift clicking circles through the widget tree by
            # choosing the parent of the currently selected widget.
            elif event.state & gtk.gdk.SHIFT_MASK:
                parent = get_parent(self)
                parent.project.selection.circle(self)

            # Control clicking adds or removes the widget from the
            # selection
            elif event.state & gtk.gdk.CONTROL_MASK:
                parent = get_parent(self)
                parent.project.selection.toggle(self)

            # otherwise we should be able to select placeholder
            # for paste operations
            else:
                parent = get_parent(self)
                parent.project.selection.set(self)

        elif event.button == 3 and event.type == gtk.gdk.BUTTON_PRESS:
            popup = PlaceholderPopup(command_manager, self)
            popup.pop(event)

        return True

    def do_popup_menu(self):
        popup = PlaceholderPopup(command_manager, self)
        popup.pop(None)
        return True

    def is_deletable(self):
        """
        Check if it's possible to delete the placeholder. Currently it
        is only possible to delete a placeholder if it's parent is a
        gtk.Box and it is not the only child.

        @return: True if it's possible to delete the placeholder
        @rtype: bool
        """
        # XXX this code is still a bit hackish and we only support
        # deleting placeholders that are part of a Box. We should look
        # into making this more generic and maybe ask the parent
        # widget (or its adaptor) if it's ok to delete the
        # placeholder.
        parent = get_parent(self)
        if not parent:
            return False

        gtk_parent = parent.widget
        if not isinstance(gtk_parent, gtk.Box):
            return False

        return len(gtk_parent.get_children()) > 1

gobject.type_register(Placeholder)

if __name__ == '__main__':
    win = gtk.Window()
    win.connect('destroy', gtk.main_quit)

    p = Placeholder()
    win.add(p)
    win.show_all()

    gtk.main()
