"""Set of missing GTK+ macros and functions"""
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

import gtk

def widget_realized(widget):
    """Equivalent to the GTK_WIDGET_REALIZED macro"""
    return (widget.flags() & gtk.REALIZED) != 0

def widget_visible(widget):
    """Equivalent to the GTK_WIDGET_VISIBLE macro"""
    return (widget.flags() & gtk.VISIBLE) != 0

def widget_mapped(widget):
    """Equivalent to the GTK_WIDGET_MAPPED macro"""
    return (widget.flags() & gtk.MAPPED) != 0

def widget_drawable(widget):
    """Equivalent to the GTK_WIDGET_DRAWABLE macro"""
    return widget_visible(widget) and widget_mapped(widget)

def widget_sensitive(widget):
    """Equivalent to the GTK_WIDGET_SENSITIVE macro"""
    return (widget.flags() & gtk.SENSITIVE) != 0

def widget_parent_sensitive(widget):
    """Equivalent to the GTK_WIDGET_PARENT_SENSITIVE macro"""
    return (widget.flags() & gtk.PARENT_SENSITIVE) != 0

def widget_is_sensitive(widget):
    """Equivalent to the GTK_WIDGET_IS_SENSITIVE macro"""
    return widget_sensitive(widget) and widget_parent_sensitive(widget)

def widget_toplevel(widget):
    """Equivalent to the GTK_WIDGET_TOPLEVEL macro"""
    return (widget.flags() & gtk.TOPLEVEL) != 0

def widget_no_window(widget):
    """Equivalent to the GTK_WIDGET_NO_WINDOW macro"""
    return (widget.flags() & gtk.NO_WINDOW) != 0

def get_event_widget(event):
    """Equivalent to the gtk_get_event_widget function"""
    if (event and event.window):
        return event.window.get_user_data()

def clamp(value, low, high):
    """Return value limited to the range [low,hign]"""
    if value < low:
        return low
    if value > high:
        return high
    return value


def popup_grab_on_window(window, activate_time, grab_keyboard):
    """Do a grab on the gdk window"""
    mask = (gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK |
            gtk.gdk.POINTER_MOTION_MASK)
    if (gtk.gdk.pointer_grab(window, True, mask, None, None, activate_time) ==
        gtk.gdk.GRAB_SUCCESS):
        if (not grab_keyboard or
            gtk.gdk.keyboard_grab(window, True, activate_time) ==
            gtk.gdk.GRAB_SUCCESS):
            return True
        else:
            display = window.get_display()
            display.pointer_ungrab(activate_time)
            return False

    return False
