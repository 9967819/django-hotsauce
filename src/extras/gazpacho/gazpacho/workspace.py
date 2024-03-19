# Copyright (C) 2004,2005 by SICEm S.L.
# Copyright (C) 2005 Red Hat, Inc.
# Copyright (C) 2006 Async Open Source
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
import pango
import gtk
from gtk import gdk

class WorkSpaceChild(object):
    """Attributes of a child widget stored in WorkSpace"""

    DECORATION_PAD = 5

    def __init__(self, widget):
        self.layout = None
        self.widget = widget
        self.x = 40
        self.y = 40
        self.window_x = 0
        self.window_y = 0
        self.title_height = 0
        self.decoration_x = 0
        self.decoration_y = 0
        self.decoration_width = 1
        self.decoration_height = 1

    def set_parent(self, parent):
        self.layout = parent.create_pango_layout('')
        self.layout.set_ellipsize(pango.ELLIPSIZE_END)
        self.layout.set_alignment(pango.ALIGN_LEFT)
        self.widget.set_parent(parent)

    def set_title(self, title):
        self.layout.set_text(title)
        extents = self.layout.get_pixel_extents()
        self.title_height = extents[1][3]

    def compute_size(self):
        parent = self.widget.get_parent()
        self.window_x = self.x + parent.allocation.x + parent.border_width
        self.window_y = self.y + parent.allocation.y + parent.border_width
        self.decoration_x = self.window_x - self.DECORATION_PAD
        self.decoration_y = (self.window_y -
                             self.DECORATION_PAD*2 - self.title_height)
        w, h = self.widget.size_request()
        self.decoration_width = w + self.DECORATION_PAD*2
        self.decoration_height = (h + self.DECORATION_PAD*2 +
                                  self.title_height + self.DECORATION_PAD)
        self.layout.set_width(w * pango.SCALE)

    def window_point_in_decoration(self, x, y):
        if y < self.decoration_y:
            return False
        elif y > self.decoration_y + self.decoration_height:
            return False
        elif x < self.decoration_x:
            return False
        elif x > self.decoration_x + self.decoration_width:
            return False
        elif y < self.window_y:
            return True
        elif x < self.decoration_x + self.DECORATION_PAD:
            return True
        elif x > (self.decoration_x +
                  self.decoration_width - self.DECORATION_PAD):
            return True
        elif y > (self.decoration_y +
                  self.decoration_height - self.DECORATION_PAD):
            return True
        else:
            return False

    def window_point_resize(self, x, y):
        if (x > (self.decoration_x +
                 self.decoration_width -
                 self.DECORATION_PAD) and
            y > (self.decoration_y +
                 self.decoration_height -
                 self.DECORATION_PAD)):
            return True
        return False

def set_adjustment_upper(adj, upper, always_emit):
    changed = False
    value_changed = False

    min = max(0.0, upper - adj.page_size)

    if upper != adj.upper:
        adj.upper = upper
        changed = True

    if adj.value > min:
        adj.value = min
        value_changed = True

    if changed or always_emit:
        adj.changed()
    if value_changed:
        adj.value_changed()

def new_adj():
    return gtk.Adjustment(0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0)

(CHILD_NONE,
 CHILD_MOVE,
 CHILD_RESIZE) = list(range(3))

class WorkSpace(gtk.Container):
    __gsignals__ = dict(set_scroll_adjustments=
                        (gobject.SIGNAL_RUN_LAST, None,
                         (gtk.Adjustment, gtk.Adjustment)))
    def __init__(self):
        self._children = []
        self._moving_child = None
        self._moving_start_x_pointer = 0
        self._moving_start_y_pointer = 0
        self._moving_start_x_position = 0
        self._moving_start_y_position = 0
        self._action_type = CHILD_NONE
        self._width = 100
        self._height = 100
        self._hadj = None
        self._vadj = None
        self._vadj_changed_id = -1
        self._hadj_changed_id = -1
        self._bin_window = None

        gtk.Container.__init__(self)
        self.add_events(gdk.BUTTON_PRESS_MASK)

        if not self._hadj or not self._vadj:
            self._set_adjustments(self._vadj or new_adj(),
                                  self._hadj or new_adj())

    # Public API
    def set_size(self, width, height):
        if self._width != width:
            self._width = width
        if self._height != height:
            self._height = height
        if self._hadj:
            set_adjustment_upper(self._hadj, self._width, False)
        if self._vadj:
            set_adjustment_upper(self._vadj, self._height, False)

        if self.flags() & gtk.REALIZED:
            self._bin_window.resize(max(width, self.allocation.width),
                                    max(height, self.allocation.height))

    def set_widget_title(self, widget, title):
        """
        @param widget:
        @param title:
        """
        child = self._get_child_from_widget(widget)
        child.set_title(title)
        if child.widget.flags() & gtk.VISIBLE:
            self.queue_resize()

    def set_child_position(self, widget, x, y):
        """
        @param widget:
        @param x:
        @param y:
        """
        child = self._get_child_from_widget(widget)
        self._set_child_position(child, x, y)

    # Child callbacks
    def _on_child_realize(self, window):
        window.window = gdk.Window(
            window.get_parent_window(),
            window_type=gdk.WINDOW_CHILD,
            x=window.allocation.x,
            y=window.allocation.y,
            width=window.allocation.width,
            height=window.allocation.height,
            wclass=gdk.INPUT_OUTPUT,
            visual=window.get_visual(),
            colormap=window.get_colormap(),
            event_mask=(window.get_events() |
                        (gdk.EXPOSURE_MASK |
                         gdk.BUTTON_PRESS_MASK |
                         gdk.BUTTON_RELEASE_MASK |
                         gdk.KEY_PRESS_MASK |
                         gdk.KEY_RELEASE_MASK |
                         gdk.ENTER_NOTIFY_MASK |
                         gdk.LEAVE_NOTIFY_MASK |
                         gdk.STRUCTURE_MASK)))
        window.window.set_user_data(self)
        window.style.attach(window.window)

        window.window.enable_synchronized_configure()

    def _on_child_size_allocate(self, window, allocation):
        window.allocation = allocation
        if window.flags() & gtk.REALIZED:
            window.window.move_resize(*allocation)

        if window.child and window.child.flags() & gtk.VISIBLE:
            child_allocation = (
                window.border_width,
                window.border_width,
                max(1, window.allocation.width - window.border_width * 2),
                max(1, window.allocation.height - window.border_width * 2))
            window.child.size_allocate(child_allocation)

    # Private

    def _set_child_position(self, child, x, y, resize=True):
        if child.x != x or child.y != y:
            child.x, child.y = x, y

            if resize and child.widget.flags() & gtk.VISIBLE:
                self.queue_resize()

    def _get_child_from_widget(self, widget):
        for child in self._children:
            if child.widget == widget:
                return child
        else:
            raise AssertionError

    def _pick_child(self, window_x, window_y):
        reversed = list(self._children)
        reversed.reverse()
        for c in reversed:
            if c.window_point_in_decoration(window_x, window_y):
                return c
        return None

    def _begin_move_child(self, child, x, y, time):
        if self._moving_child != None:
            raise AssertionError("can't move two children at once")

        mask = (gdk.BUTTON_RELEASE_MASK | gdk.BUTTON_RELEASE_MASK |
                gdk.POINTER_MOTION_MASK)
        grab = gdk.pointer_grab(self.window, False, mask, None, None,
                                int(time))
        if grab != gdk.GRAB_SUCCESS:
            raise AssertionError("grab failed")

        self._children.remove(child)
        self._children.append(child)

        self._moving_child = child
        self._moving_start_x_pointer = x
        self._moving_start_y_pointer = y
        self._moving_start_x_position = child.x
        self._moving_start_y_position = child.y
        w, h = child.widget.get_size_request()
        self._moving_start_w, self._moving_start_h = w, h

    def _update_move_child (self, x, y):
        child = self._moving_child
        if not child:
            return

        dx = x - self._moving_start_x_pointer
        dy = y - self._moving_start_y_pointer
        if self._action_type == CHILD_MOVE:
            self._set_child_position(child,
                                     self._moving_start_x_position + dx,
                                     self._moving_start_y_position + dy)

        if self._action_type == CHILD_RESIZE:
            child.widget.set_size_request(self._moving_start_w + dx,
                                          self._moving_start_h + dy)

            self.queue_draw()

    def _end_move_child(self, time):
        if not self._moving_child:
            return

        gdk.pointer_ungrab(int(time))
        self._moving_child = None

    def _set_adjustments(self, hadj, vadj):
        if not hadj and self._hadj:
            hadj = new_adj()

        if not vadj and self._vadj:
            vadj = new_adj()

        if self._hadj and self._hadj != hadj:
            self._hadj.disconnect(self._hadj_changed_id)

        if self._vadj and self._vadj != vadj:
            self._vadj.disconnect(self._vadj_changed_id)

        need_adjust = False

        if self._hadj != hadj:
            self._hadj = hadj
            set_adjustment_upper(hadj, self._width, False)
            self._hadj_changed_id = hadj.connect(
                "value-changed",
                self._adjustment_changed)
            need_adjust = True

        if self._vadj != vadj:
            self._vadj = vadj
            set_adjustment_upper(vadj, self._height, False)
            self._vadj_changed_id = vadj.connect(
                "value-changed",
                self._adjustment_changed)
            need_adjust = True

        if need_adjust and vadj and hadj:
            self._adjustment_changed()

    def _adjustment_changed(self, adj=None):
        if self.flags() & gtk.REALIZED:
            self._bin_window.move(int(-self._hadj.value),
                                  int(-self._vadj.value))
            self._bin_window.process_updates(True)

    # GtkWidget

    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(self.get_parent_window(),
                                 width=self.allocation.width,
                                 height=self.allocation.height,
                                 window_type=gdk.WINDOW_CHILD,
                                 wclass=gdk.INPUT_OUTPUT,
                                 event_mask=(self.get_events() |
                                             gdk.EXPOSURE_MASK))
        self.window.set_user_data(self)
        self.window.move_resize(*self.allocation)

        self._bin_window = gdk.Window(
            self.window,
            window_type=gdk.WINDOW_CHILD,
            x=int(-self._hadj.value),
            y=int(-self._vadj.value),
            width=max(self._width, self.allocation.width),
            height=max(self._height, self.allocation.height),
            colormap=self.get_colormap(),
            wclass=gdk.INPUT_OUTPUT,
            event_mask=(self.get_events() | gdk.EXPOSURE_MASK |
                        gdk.SCROLL_MASK))
        self.style.set_background(self._bin_window, gtk.STATE_NORMAL)
        self._bin_window.set_user_data(self)

        self.set_style(self.style.attach(self.window))

        for child in self._children:
            child.widget.set_parent_window(self._bin_window)

    def do_unrealize(self):
        self._bin_window.set_user_data(None)
        self._bin_window = None
        self.window.set_user_data(None)

    def do_expose_event(self, event):
        window = event.window

        gc = gdk.GC(window)
        gc.set_rgb_fg_color(self.style.text[self.state])

        for c in self._children:
            window.draw_rectangle(self.style.base_gc[self.state], True,
                                  c.decoration_x, c.decoration_y,
                                  c.decoration_width, c.decoration_height)
            window.draw_rectangle(gc, False,
                                  c.decoration_x, c.decoration_y,
                                  c.decoration_width, c.decoration_height)

            window.draw_line(gc,
                             c.decoration_x,
                             c.window_y - c.DECORATION_PAD,
                             c.decoration_x + c.decoration_width,
                             c.window_y - c.DECORATION_PAD)

            window.draw_layout(gc,
                               c.decoration_x + c.DECORATION_PAD,
                               c.decoration_y + c.DECORATION_PAD - 2,
                               c.layout)

            self.propagate_expose(c.widget, event)

    def do_map(self):
        self.set_flags(self.flags() | gtk.MAPPED)
        for child in self._children:
            flags = child.widget.flags()
            if flags & gtk.VISIBLE:
                if not (flags & gtk.MAPPED):
                    child.widget.map()
        self._bin_window.show()
        self.window.show()

    def do_size_request(self, req):
        req.width = 0
        req.height = 0

        for child in self._children:
            if child.widget.flags() & gtk.VISIBLE:
                child.compute_size()
                req.width = max(req.width,
                                child.decoration_x + child.decoration_width)
                req.height = max(req.height,
                                 child.decoration_y + child.decoration_height)
            child.widget.size_request()

        req.width = req.width + self.border_width * 2
        req.height = req.height + self.border_width * 2

    def do_size_allocate(self, allocation):
        self.allocation = allocation
        for c in self._children:
            if c.widget.flags() & gtk.VISIBLE:
                child_req = c.widget.get_child_requisition()
                w, h = child_req
                c.widget.size_allocate((c.window_x, c.window_y, w, h))

        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)
            self._bin_window.resize(max(self._width, allocation.width),
                                    max(self._height, allocation.height))

        self._hadj.page_size = allocation.width
        self._hadj.page_increment = allocation.width * 0.9
        self._hadj.lower = 0
        set_adjustment_upper(self._hadj,
                             max(allocation.width, self._width), True)

        self._vadj.page_size = allocation.height
        self._vadj.page_increment = allocation.height * 0.9
        self._vadj.lower = 0
        self._vadj.upper = max(allocation.height, self._height)
        set_adjustment_upper(self._vadj,
                             max(allocation.height, self._height), True)

    def do_set_scroll_adjustments(self, hadj, vadj):
        self._set_adjustments(hadj, vadj)

    def do_key_press_event(self, event):
        if event.keyval == gtk.keysyms.Escape:
            self._end_move_child(event.time)

    def do_button_press_event(self, event):
        if self._moving_child != None:
            return

        x, y = int(event.x), int(event.y)

        child = self._pick_child(x, y)
        if child == None:
            return

        if child.window_point_resize(x, y):
            self._action_type = CHILD_RESIZE
        else:
            self._action_type = CHILD_MOVE

        self._begin_move_child(child, x, y, event.time)

    def do_button_release_event(self, event):
        self._update_move_child(int(event.x), int(event.y))
        self._end_move_child(event.time)

    def do_motion_notify_event(self, event):
        if self._moving_child != None:
            self._update_move_child(int(event.x), int(event.y))

    # GtkContainer

    def do_forall(self, internals, callback, data):
        for child in self._children:
            callback(child.widget, data)

    def do_add(self, widget):
        child = WorkSpaceChild(widget)
        self._children.append(child)
        if self.flags() & gtk.REALIZED:
            widget.set_parent_window(self._bin_window)

        widget.connect('realize', self._on_child_realize)
        widget.connect('size-allocate', self._on_child_size_allocate)

        if isinstance(widget, gtk.Window):
            widget.unset_flags(gtk.TOPLEVEL)
            widget.set_resize_mode(gtk.RESIZE_PARENT)
            widget.set_size_request(300, 200)

        child.set_parent(self)

        if widget.flags() & gtk.VISIBLE:
            self.queue_resize()
        self.queue_draw()

    def do_remove(self, widget):
        child = self._get_child_from_widget(widget)

        if self._moving_child == child:
            self._end_move_child(0)

        was_visible = widget.flags() & gtk.VISIBLE
        self._children.remove(child)
        widget.unparent()

        if was_visible:
            self.queue_resize()
        self.queue_draw()

if gtk.pygtk_version >= (2, 8):
    WorkSpace.set_set_scroll_adjustments_signal('set-scroll-adjustments')

gobject.type_register(WorkSpace)

class EmbeddableMessageDialog(gtk.MessageDialog):
    """Message dialog with crazy hacks so you can embed it as a non-toplevel"""

    ### FIXME this class has to be generalized to all kinds of toplevel window,
    ### which should be trivial
    ### A better approach might be to do this entirely via signal
    ### connection rather
    ### than via subclass. Then you could have a make_embeddable() function
    ### that took any toplevel.

    __gsignals__ = {
        'realize': 'override',
        'size-allocate' : 'override',
        'show' : 'override',
        'hide' : 'override',
        'map' : 'override',
        'unmap' : 'override'
        }

    def __init__(self):
        #gtk.MessageDialog.__init__(self,
        #                           type=gtk.MESSAGE_INFO,
        #                           buttons=gtk.BUTTONS_OK)
        constructor = gobject.GObject.__init__
        constructor(self, message_type=gtk.MESSAGE_INFO,
                    buttons=gtk.BUTTONS_OK)
        self.label.set_text('Hello')

        self.unset_flags(gtk.TOPLEVEL)

    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)

        self.window = gdk.Window(
            self.get_parent_window(),
            window_type=gdk.WINDOW_CHILD,
            x=self.allocation.x,
            y=self.allocation.y,
            width=self.allocation.width,
            height=self.allocation.height,
            wclass=gdk.INPUT_OUTPUT,
            visual=self.get_visual(),
            colormap=self.get_colormap(),
            event_mask=(self.get_events() | gdk.EXPOSURE_MASK |
                        gdk.KEY_PRESS_MASK | gdk.KEY_RELEASE_MASK |
                        gdk.ENTER_NOTIFY_MASK | gdk.LEAVE_NOTIFY_MASK |
                        gdk.STRUCTURE_MASK))

        self.window.set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)

        self.window.enable_synchronized_configure()

    def do_size_allocate(self, allocation):
        self.allocation = allocation
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

        if self.child and self.child.flags() & gtk.VISIBLE:
            child_allocation = (
                self.border_width,
                self.border_width,
                max(1, self.allocation.width - self.border_width * 2),
                max(1, self.allocation.height - self.border_width * 2))
            self.child.size_allocate (child_allocation)

    def do_show(self):
        gtk.Bin.do_show(self)

    def do_hide(self):
        gtk.Bin.do_hide(self)

    def do_map(self):
        gtk.Bin.do_map(self)

    def do_unmap(self):
        gtk.Bin.do_unmap(self)

def main():
    window = gtk.Window()
    window.connect('delete-event', gtk.main_quit)
    window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
    window.set_size_request(500, 500)
    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    window.add(sw)

    table = WorkSpace()
    table.set_border_width(20)

    sw.add_with_viewport(table)

    dialog = EmbeddableMessageDialog()

    table.add(dialog)

    button = gtk.Button("A Button")
    table.add(button)

    table.show_all()
    req = table.size_request()
    window.set_default_size(req[0] + 10, req[1] + 10)
    window.show_all()

    gtk.main()

if __name__ == '__main__':
    main()
