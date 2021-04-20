# Copyright (C) 2005 Red Hat, Inc.
#               2005 Johan Dahlin
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

import random

import gtk
from gtk import gdk

from gazpacho.util import get_parent

use_cairo = False
try:
    from cairo import gtk as cairogtk
    use_cairo = True
except ImportError:
    pass

SELECTION_NODE_SIZE = 7
BORDER_WIDTH = 3

class IAnnotate:
    def __init__(self, widget, window):
        pass

    def draw_notes(self, x, y, width, height):
        pass

    def draw_border(self, x, y, width, height, color):
        pass

class CairoAnnotator(object):
    def __init__(self, widget, window):
        self._cr = cairogtk.gdk_cairo_create(window)
        self._cr.set_line_width(1.0)

    def draw_nodes(self, x, y, width, height):
        cr = self._cr

        cr.set_source_rgba(0.40, 0.0, 0.0, 0.75) # translucent dark red

        if width > SELECTION_NODE_SIZE and height > SELECTION_NODE_SIZE:
            cr.rectangle(x + 1, y + 1,
                         SELECTION_NODE_SIZE - 1, SELECTION_NODE_SIZE - 1)
            cr.rectangle(x + 1, y + height -SELECTION_NODE_SIZE,
                         SELECTION_NODE_SIZE - 1, SELECTION_NODE_SIZE - 1)
            cr.rectangle(x + width - SELECTION_NODE_SIZE, y + 1,
                         SELECTION_NODE_SIZE - 1, SELECTION_NODE_SIZE - 1)
            cr.rectangle(x + width - SELECTION_NODE_SIZE,
                         y + height - SELECTION_NODE_SIZE,
                         SELECTION_NODE_SIZE - 1, SELECTION_NODE_SIZE -1)
            cr.fill()

        cr.rectangle(x + 0.5, y + 0.5, width - 1, height - 1)
        cr.stroke()

    def draw_border(self, x, y, width, height, color):
        cr = self._cr

        for i in range(0, BORDER_WIDTH):
            if (i <= BORDER_WIDTH / 2):
                alpha = (i + 1.) / (BORDER_WIDTH)
            else:
                alpha = (BORDER_WIDTH - i + 0.) / (BORDER_WIDTH)

            cr.set_source_rgba(color[0], color[1], color[2],
                               alpha)
            cr.rectangle(x - BORDER_WIDTH / 2 + i + 0.5,
                         y - BORDER_WIDTH / 2 + i + 0.5,
                         width + 2 * (BORDER_WIDTH / 2 - i) - 1,
                         height + 2 * (BORDER_WIDTH / 2 - i) - 1)
            cr.stroke()

class GdkAnnotator(object):
    def __init__(self, widget, window):
        self._widget = widget
        self._window = window
        self._gc = gdk.GC(window, line_width=BORDER_WIDTH)

    def draw_nodes(self, x, y, width, height):
        window = self._window
        gc = self._widget.style.black_gc

        if width > SELECTION_NODE_SIZE and height > SELECTION_NODE_SIZE:
            window.draw_rectangle(gc, True, x, y,
                                  SELECTION_NODE_SIZE, SELECTION_NODE_SIZE)
            window.draw_rectangle(gc, True, x, y + height -SELECTION_NODE_SIZE,
                                  SELECTION_NODE_SIZE, SELECTION_NODE_SIZE)
            window.draw_rectangle(gc, True, x + width - SELECTION_NODE_SIZE, y,
                                  SELECTION_NODE_SIZE, SELECTION_NODE_SIZE)
            window.draw_rectangle(gc, True, x + width - SELECTION_NODE_SIZE,
                                  y + height - SELECTION_NODE_SIZE,
                                  SELECTION_NODE_SIZE, SELECTION_NODE_SIZE)
        window.draw_rectangle(gc, False, x, y, width - 1, height - 1)

    def draw_border(self, x, y, width, height, color):
        gc = self._gc
        gc.set_rgb_fg_color(gdk.Color(int(color[0] * 65535.999),
                                      int(color[1] * 65535.999),
                                      int(color[2] * 65535.999)))

        self._window.draw_rectangle(gc, False,
                                    x - (BORDER_WIDTH / 2),
                                    y - (BORDER_WIDTH / 2),
                                    width, height)

if use_cairo:
    Annotator = CairoAnnotator
else:
    Annotator = GdkAnnotator

def _get_window_positioned_in(widget):
    """This returns the window that the given widget's allocation is
    relative to.
    Usually this is widget.get_parent_window(). But if the widget is a
    toplevel, we use its own window, as it doesn't have a parent."""
    if widget.get_parent():
        return widget.get_parent_window()
    else:
        return widget.window

def _calculate_window_offset(gdkwindow):
    """ This calculates the offset of the given window within its toplevel.
    It also returns the toplevel """
    x = y = 0
    window = gdkwindow
    while window:
        if window.get_window_type() != gtk.gdk.WINDOW_CHILD:
            break
        tmp_x, tmp_y = window.get_position()
        x += tmp_x
        y += tmp_y
        window = window.get_parent()

    return window, x, y

def _get_border_color(widget):
    if not isinstance(widget, (gtk.Box, gtk.Table)):
        return None

    if not (widget.parent):
        return None

    if isinstance(widget.parent, (gtk.Notebook, gtk.Window)):
        return None

    colors = [(1, 0, 0),
              (0, 1, 0),
              (0, 0, 1),
              (1, 1, 0),
              (0, 0.6, 0.6),
              (1, 0.5, 0)]

    index = widget.get_data("gazpacho-border-color")
    if index == None:
        index = random.randint(0, len(colors) - 1)
        widget.set_data("gazpacho-border-color", index)

    return colors[index]

def _draw_box_borders(project, widget, expose_win, annotator):
    if not project._app._show_structure:
        return

    if not isinstance(widget, gtk.Container):
        return

    if not widget.flags() & gtk.MAPPED:
        return

    border_win = _get_window_positioned_in(widget)
    _, border_x, border_y = _calculate_window_offset(border_win)
    _, expose_x, expose_y = _calculate_window_offset(expose_win)

    if isinstance(widget, gtk.Button):
        return

    color = _get_border_color(widget)
    if color:
        allocation = widget.allocation
        annotator.draw_border(border_x + allocation.x - expose_x,
                              border_y + allocation.y - expose_y,
                              allocation.width,
                              allocation.height,
                              color)

    children = widget.get_children()
    for child in children:
        _draw_box_borders(project, child, expose_win, annotator)

def _can_draw_nodes(sel_widget, expose_win):
    """ This returns True if it is OK to draw the selection nodes for the given
    selected widget inside the given window that has received an expose event.
    This is true if the expose window is a descendent of the window to which
    widget->allocation is relative. (The check for a descendent preserves
    clipping in a situation like a viewport) """

    sel_win = _get_window_positioned_in(sel_widget)
    window = expose_win
    while window:
        if window == sel_win:
            return True
        window = window.get_parent()

    return False

def _draw_nodes(project, expose_widget, expose_win, annotator):
    """ This is called to redraw any selection nodes that intersect the given
    exposed window.  It steps through all the selected widgets, converts the
    coordinates so they are relative to the exposed window, then calls
    _draw_nodes if appropriate """

    # Calculate the offset of the expose window within its toplevel
    expose_toplevel, expose_win_x, expose_win_y = \
                     _calculate_window_offset(expose_win)

    expose_win_w, expose_win_h = expose_win.get_size()

    # Step through all the selected widgets in the project
    for sel_widget in project.selection:
        sel_win = _get_window_positioned_in(sel_widget)

        if sel_win is None:
            continue

        # Calculate the offset of the selected widget's window within
        # its toplevel
        sel_toplevel, sel_x, sel_y = _calculate_window_offset(sel_win)

        # We only draw the nodes if the window that got the expose event is
        # in the same toplevel as the selected widget
        if (expose_toplevel == sel_toplevel and
            _can_draw_nodes(sel_widget, expose_win)):
            x = sel_x + sel_widget.allocation.x - expose_win_x
            y = sel_y + sel_widget.allocation.y - expose_win_y
            w = sel_widget.allocation.width
            h = sel_widget.allocation.height

            # Draw the selection nodes if they intersect the
            # expose window bounds
            if (x < expose_win_w and x + w >= 0 and
                y < expose_win_h and y + h >= 0):
                annotator.draw_nodes(x, y, w, h)

def draw_annotations(expose_widget, expose_win):
    """ This is called to redraw any gazpacho annotations that intersect
    the given exposed window. We only draw nodes on windows that are
    actually owned by the widget. This keeps us from repeatedly
    drawing nodes for the same window in the same expose event. """

    from gazpacho.gadget import Gadget

    expose_gadget = Gadget.from_widget(expose_widget)
    if not expose_gadget:
        expose_gadget = get_parent(expose_widget)
    if not expose_gadget:
        return False

    project = expose_gadget.project

    if not expose_win.is_viewable():
        return False

    # Find the corresponding widget and gadget
    if expose_widget != expose_win.get_user_data():
        return False

    annotator = Annotator(expose_widget, expose_win)

    _draw_box_borders(project, expose_widget.get_toplevel(),
                      expose_win, annotator)
    _draw_nodes(project, expose_widget, expose_win, annotator)
