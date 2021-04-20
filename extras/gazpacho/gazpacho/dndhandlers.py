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

import gtk

from gazpacho import gapi, util
from gazpacho.command import Command
from gazpacho.clipboard import CommandCutPaste
from gazpacho.commandmanager import command_manager
from gazpacho.gadget import Gadget
from gazpacho.i18n import _
from gazpacho.placeholder import Placeholder
from gazpacho.widgets.base.box import DragAppendCommand, CreateAppendCommand, \
     DragExtendCommand, CreateExtendCommand

(DND_POS_INVALID,
 DND_POS_TOP,
 DND_POS_BOTTOM,
 DND_POS_LEFT,
 DND_POS_RIGHT,
 DND_POS_BEFORE,
 DND_POS_AFTER) = list(range(7))

(INFO_TYPE_XML,
 INFO_TYPE_WIDGET,
 INFO_TYPE_PALETTE) = list(range(3))

MIME_TYPE_OBJECT_XML = 'application/x-gazpacho-object-xml'
MIME_TYPE_OBJECT     = 'application/x-gazpacho-object'
MIME_TYPE_OBJECT_PALETTE = 'application/x-gazpacho-palette'

# This is the value returned by Widget.drag_dest_find_target when no
# targets have been found. The API reference says it should return
# None (and NONE) but it seems to return the string "NONE".
DND_NO_TARGET = "NONE"

DND_WIDGET_TARGET  = (MIME_TYPE_OBJECT, gtk.TARGET_SAME_APP, INFO_TYPE_WIDGET)
DND_XML_TARGET     = (MIME_TYPE_OBJECT_XML, 0, INFO_TYPE_XML)
DND_PALETTE_TARGET = (MIME_TYPE_OBJECT_PALETTE, gtk.TARGET_SAME_APP,
                      INFO_TYPE_PALETTE)

class DnDHandler(object):
    """
    The DnDHandler is responsible for handling events related to
    moving or copying widget by drag and drop.

    It might be worth mentioning a few things about the naming
    convention used in the implementation. This mainly concern the
    widgets that are participating in the drag and drop related
    activities.

    First we have the source widget. This is the widget that is being
    dragged and it is the top-most (non-internal and non-hidden)
    widget that has been clicked on. Unfortunately not all widgets can
    receive the necessary drag/drop events and thus another widget
    might be the one that received these events. This widget is
    referred to as the source event widget. The source event widget
    will calculate the source widget and keep a reference to it.

    Then there is the target widget. This is the widget onto which the
    source widget will be dropped. As with the source widget, the
    target widget might not be able to receive the drag/drop events
    and thus another widget will receive them in its place. This
    widget is referred to as the target event widget. The target
    widget has to be calculated when it is needed.

    If it will be clear from the context, the source event widget and
    target event widget will sometimes be referred to as the event
    widget.
    """

    # XXX what happens when we leave a target widget and enters a new
    #     target widget when both target widgets are children of the
    #     same target event widget? This would probably only affect
    #     the clearing of the drag highlight, if it matters at all.

    # XXX there seems to be some problems with gtk.Entry. It's
    #      possible to drag it onto itself when clicking on the actual
    #      text entry and dragging it near the edge of the entry. See
    #      _on_widget__drag_data_received for more info

    #
    # Public methods
    #

    def connect_drag_handlers(self, widget):
        """
        Connect all handlers necessary for the widget to serve as a
        drag source.

        @param widget: widget to which the handlers should be connected
        @type widget: gtk.Widget
        """
        widget.drag_source_set(gtk.gdk.BUTTON1_MASK,
                               [DND_WIDGET_TARGET, DND_XML_TARGET],
                               gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        widget.connect('drag_begin', self._on_widget__drag_begin)
        widget.connect('drag_data_get', self._on_widget__drag_data_get)


    def connect_drop_handlers(self, widget):
        """
        Connect all handlers necessary for the widget to serve as a
        drag destination.

        @param widget: widget to which the handlers should be connected
        @type widget: gtk.Widget
        """
        widget.drag_dest_set(0,
                             [DND_WIDGET_TARGET,
                              DND_XML_TARGET,
                              DND_PALETTE_TARGET],
                             gtk.gdk.ACTION_MOVE | gtk.gdk.ACTION_COPY)
        widget.connect('drag_motion', self._on_widget__drag_motion)
        widget.connect('drag_leave', self._on_widget__drag_leave)
        widget.connect('drag_drop', self._on_widget__drag_drop)
        widget.connect('drag_data_received',
                       self._on_widget__drag_data_received)


    #
    # Methods that can be used and overridden by subclasses
    #

    def _get_target_project(self, widget):
        """
        Get the project to which the widget belongs.

        @param widget: a widget
        @type widget: gtk.Widget
        """
        raise NotImplementedError

    def _set_drag_highlight(self, event_widget, x, y):
        """Highlight the target widget in an appropriate way to
        indicate that this is a valid drop zone.

        @param event_widget: the target event widget
        @type event_widget: gtk.Widget
        @param x: the mouse x position
        @type x: int
        @param y: the mouse y position
        @type y: int
        """
        raise NotImplementedError

    def _clear_drag_highlight(self, event_widget):
        """Clear the drag highligt.

        @param event_widget: the target event widget
        @type event_widget: gtk.Widget
        """
        raise NotImplementedError

    def _is_valid_drop_zone(self, drag_context, target_event_widget, x ,y):
        """Check whether the drop zone is valid or not.

        @param drag_context: the drag context
        @type drag_context: gtk.gdk.DragContext
        @param target_event_widget: the target event widget
        @type target_event_widget: gtk.Widget
        @param x: the X position of the drop
        @type x: int
        @param y: the Y position of the drop
        @type y: int
        @return: whether or not this is a valid drop zone
        @rtype: bool
        """
        # Check if it is a valid target type
        dest_targets = target_event_widget.drag_dest_get_target_list()
        target = target_event_widget.drag_dest_find_target(drag_context,
                                                           dest_targets)
        
        if target == DND_NO_TARGET:
            return False

        # We can always drag widgets from the palette and widgets that
        # are in XML form
        if target in (MIME_TYPE_OBJECT_PALETTE, MIME_TYPE_OBJECT_XML):
            return True

        # Get the correct source widget and target widget
        source_event_widget = drag_context.get_source_widget()
        source_event_gadget = Gadget.from_widget(source_event_widget)
        source_widget = source_event_gadget.dnd_gadget.widget

        target_widget, tx, ty = self._get_target_widget(target_event_widget,
                                                        x, y)

        # We cannot drop onto ourselves
        if source_widget is target_widget:
            return False

        # Make sure we don't try to drop a widget onto one of its
        # children or parents
        if (source_widget.is_ancestor(target_widget)
            or target_widget.is_ancestor(source_widget)):
            return False

        return True

    def _get_drag_action(self, drag_context, target_event_widget):
        """Figure out which drag action should be performed.

        If the target is in the same project as the source we move the
        widget, otherwise we copy it.

        @param drag_context: the drag context
        @type drag_context: gtk.gdk.DragContext
        @param target_event_widget: the target event widget
        @type target_event_widget: gtk.Widget
        """
        # XXX doesn't it make more sense to move only when source and
        #     target is in the same toplevel?
        target_project = self._get_target_project(target_event_widget)
        source_event_widget = drag_context.get_source_widget()
        source_event_gadget = source_event_widget and Gadget.from_widget(source_event_widget)
        if(not source_event_gadget
           or source_event_gadget.project != target_project):
            return gtk.gdk.ACTION_COPY

        return gtk.gdk.ACTION_MOVE

    def _get_source_gadget(self, data, info, drag_context, project):
        """Get the gadget for the source widget.

        This means the gadget for the widget that is being dragged,
        which is not necessarily the same widget as the one that
        recieved the drag event.

        @return: the source gadget
        @rtype: L{gazpacho.gadget.Gadget}
        """
        source_gadget = None
        if info == INFO_TYPE_WIDGET:
            event_widget = drag_context.get_source_widget()
            event_gadget = Gadget.from_widget(event_widget)
            source_gadget = event_gadget.dnd_gadget

        elif info == INFO_TYPE_XML:
            source_gadget = Gadget.from_xml(project, data.data)

        return source_gadget

    def _get_target_widget(self, event_widget, x, y):
        """Get the target widget.

        This means the widget onto which we perform the drop, which is
        not necessarily the same widget as the one that recieved the
        drop event.

        @return: the target widget and translated coordinates
        @rtype: gtk.Widget, int, int
        """
        return event_widget, x, y

    #
    # Signal handlers for the drag source
    #

    def _on_widget__drag_begin(self, event_widget, drag_context):
        """Callback for the 'drag-begin' event."""
        raise NotImplementedError

    def _on_widget__drag_data_get(self, event_widget, drag_context,
                                  selection_data, info, time):
        """Callback for the 'drag-data-get' event."""
        raise NotImplementedError


    #
    # Signal handlers for the drag target
    #

    def _on_widget__drag_leave(self, event_widget, drag_context, time):
        """Clear the drag highlight when we leave the target widget.

        This is a callback for the 'drag-leave' event.
        """
        self._clear_drag_highlight(event_widget)

    def _on_widget__drag_motion(self, event_widget, drag_context, x, y, time):
        """Decide whether this is a valid drop zone or not.

        If the drop zone is valid we set the drag highlight and the
        appropriate drag action. This is a callback for the
        'drag-motion' event.
        """
        if not self._is_valid_drop_zone(drag_context, event_widget, x, y):
            return False

        # XXX: Do not draw highlight if there is a children visible at
        #      position x, y.
        #      Test case is HBox->Notebook, drag notebook into itself, notice
        #      border which is not correct
        self._set_drag_highlight(event_widget, x, y)

        drag_action = self._get_drag_action(drag_context, event_widget)
        drag_context.drag_status(drag_action, time)
        return True

    def _on_widget__drag_drop(self, event_widget, drag_context, x, y, time):
        """Callback for handling the 'drag_drop' event."""
        if MIME_TYPE_OBJECT_PALETTE in drag_context.targets:
            mime_type = MIME_TYPE_OBJECT_PALETTE
        elif drag_context.action == gtk.gdk.ACTION_MOVE:
            mime_type = MIME_TYPE_OBJECT
        else:
            mime_type = MIME_TYPE_OBJECT_XML
        event_widget.drag_get_data(drag_context, mime_type, time)
        return True

    def _on_widget__drag_data_received(self, event_widget, drag_context,
                                       x, y, data, info, time):
        """Callback for the 'drag-data-recieved' event."""
        raise NotImplementedError

class WidgetDnDHandler(DnDHandler):

    def _get_target_widget(self, event_widget, x, y):
        """Get the target widget

        @param event_widget: the target event widget
        @type event: gtk.Widget
        @param x: the X position of the drop
        @type x: int
        @param y: the Y position of the drop
        @type y: int

        @return: the target widget
        @rtype: gtk.Widget
        """
        target_widget = self._find_deepest_child_at_position(event_widget, x, y)
        tx, ty = event_widget.translate_coordinates(target_widget, x, y)
        return target_widget,tx,ty

    def _find_deepest_child_at_position(self, widget, x, y):
        """Find the deepest child the the specified position.

        This method will ignore internal and hidden widgets.

        @return: the deepest widget
        @rtype: gtk.Widget
        """
        # XXX this code is based on Gadget._find_deepest_child_at_position
        # but we need to avoid internal and hidden widgets. Maybe it's possible
        # to merge these two methods?
        found = None
        if isinstance(widget, gtk.Container):
            # we're not interested internal or hidden widgets
            # XXX can these widgets contain children that we
            #     are interested in?            
            # XXX there is no good way to figure out which widgets are
            #     hidden at the moment.
            for child in widget.get_children():
                # hidden widget usually don't have a gadget?
                if not Gadget.from_widget(child):
                    continue
                
                child_x, child_y = widget.translate_coordinates(child, x, y)

                # sometimes the found widget is not mapped or visible
                # think about a widget in a notebook page which is not selected
                if (0 <= child_x < child.allocation.width and
                    0 <= child_y < child.allocation.height and
                    child.flags() & gtk.MAPPED):
                    found = self._find_deepest_child_at_position(child,
                                                                 child_x,
                                                                 child_y)
                    if found:
                        break

        return found or widget

    def _get_target_project(self, widget):
        """
        Get the project to which the target belongs.

        @param widget: the target widget
        @type widget: gtk.Widget
        """
        gadget = Gadget.from_widget(widget)
        return gadget.project

    def _set_drag_highlight(self, event_widget, x, y):
        """
        Highlight the widget in an appropriate way to indicate
        that this is a valid drop zone.

        @param event_widget: the target event widget
        @type event_widget: gtk.Widget
        @param x: the mouse x position
        @type x: int
        @param y: the mouse y position
        @type y: int
        """
        target_widget, tx, ty = self._get_target_widget(event_widget, x, y)
        gadget = Gadget.from_widget(target_widget)
        gadget.set_drop_region(self._get_drop_location(target_widget, tx, ty)[1])

    def _clear_drag_highlight(self, event_widget):  
        """Clear the drag highligt for the target widget.

        This method should initially be called with the target event
        widget as an argument. It will then recursively iterate
        through its own children since we don't actually know which
        whidget is the target widget.

        @param event_widget: the target event widget
        @type event_widget: gtk.Widget
        """
        gadget = Gadget.from_widget(event_widget)
        if gadget:
            gadget.clear_drop_region()

        if isinstance(event_widget, gtk.Container):
            children = util.get_all_children(event_widget)
            for child in children:
                self._clear_drag_highlight(child)


    def _is_valid_drop_zone(self, drag_context, target_event_widget, x ,y):
        """Check whether the drop zone is valid or not.

        This behaves as in the super class but it also checks if we
        are in a valid location (i.e. not in the middle of the widget)

        @param drag_context: the drag context
        @type drag_context: gtk.gdk.DragContext
        @param target_event_widget: the target event widget
        @type target_event_widget: gtk.Widget
        @param x: the X position of the drop
        @type x: int
        @param y: the Y position of the drop
        @type y: int
        @return: whether or not this is a valid drop zone
        @rtype: bool
        """
        if not DnDHandler._is_valid_drop_zone(self, drag_context,
                                              target_event_widget, x, y):
            return False

        # we need to make sure that we actually are in a valid location
        target_widget,tx,ty = self._get_target_widget(target_event_widget,x,y)
        location = self._get_drop_location(target_widget, tx, ty)[0]
        return location != DND_POS_INVALID

    def _get_drop_location(self, target_widget, x, y):
        """Calculate the drop region and also the drop location
        relative to the widget.

        The location can be one of the following constants
          - DND_POS_INVALID
          - DND_POS_TOP
          - DND_POS_BOTTOM
          - DND_POS_LEFT
          - DND_POS_RIGHT
          - DND_POS_BEFORE
          - DND_POS_AFTER

        The drop region is a tuple of x,y,width and height.

        @param target_widget: the widget where the drop occurred
        @type target_widget: gtk.Widget
        @param x: the X position of the drop
        @type x: int
        @param y: the Y position of the drop
        @type y: int

        @return: (location, region)
        @rtype: tuple
        """
        parent = util.get_parent(target_widget)
        h_appendable = parent and isinstance(parent.widget, gtk.HBox)
        v_appendable = parent and isinstance(parent.widget, gtk.VBox)

        x_off, y_off, width, height = target_widget.allocation
        x_third = width / 3
        y_third = height / 3

        if x > x_third * 2:
            if h_appendable:
                location = DND_POS_AFTER
            else:
                location = DND_POS_RIGHT
            region = (x_third * 2 + x_off, 2 + y_off,
                      x_third, height - 4)
        elif x < x_third:
            if h_appendable:
                location = DND_POS_BEFORE
            else:
                location = DND_POS_LEFT
            region = (2 + x_off, 2 + y_off, x_third - 2, height - 4)
        elif y > y_third * 2:
            if v_appendable:
                location = DND_POS_AFTER
            else:
                location = DND_POS_BOTTOM
            region = (2 + x_off, y_third * 2 + y_off, width - 4, y_third - 2)
        elif y < y_third:
            if v_appendable:
                location = DND_POS_BEFORE
            else:
                location = DND_POS_TOP
            region = (2 + x_off, 2 + y_off, width - 4, y_third)
        else:
            location = DND_POS_INVALID
            region = (0, 0, 0, 0)

        return location, region

    def _is_extend_action(self, location):
        """
        Check if we should perform an extend action.

        @param location: the drop location
        @type location: dnd constant
        @return: True if we should extend
        @rtype: bool
        """
        return location in (DND_POS_TOP, DND_POS_BOTTOM, DND_POS_LEFT,
                            DND_POS_RIGHT)

    def _is_append_action(self, location):
        """
        Check if we should perform an append action.

        @param location: the drop location
        @type location: dnd constant
        @return: True if we should append
        @rtype: bool
        """
        return location in (DND_POS_AFTER, DND_POS_BEFORE)

    def _get_append_position(self, target_widget, location):
        """
        Get the position where we should add the widget.

        @param target_widget: the widget where the drop occurred
        @type target_widget: gtk.Widget
        @param location: the drop location
        @type location: dnd constant
        """
        box = target_widget.get_parent()
        pos = box.get_children().index(target_widget)
        if location == DND_POS_AFTER:
            pos = pos + 1
        return pos

    def _execute_drag(self, location, source_gadget, target_gadget, keep_source):
        """
        Execute the drag-append or drag-extend command.

        @param location: the drop location
        @type location: dnd constant
        @param source_gadget: the gadget that is being dragged
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param target_gadget: the gadget where the drop occurred
        @type target_gadget: L{gazpacho.gadget.Gadget}
        @param keep_source: True if the source widget should not be removed
        @type keep_source: bool

        @return: True if the drop was successful
        @rtype: bool
        """
        if not source_gadget:
            return False

        if self._is_extend_action(location):
            cmd = DragExtendCommand(source_gadget, target_gadget, location,
                                    keep_source)
            command_manager.execute(cmd, target_gadget.project)
            return True

        elif self._is_append_action(location):
            pos = self._get_append_position(target_gadget.widget, location)
            parent = target_gadget.get_parent()
            cmd = DragAppendCommand(source_gadget, parent, pos, keep_source)
            command_manager.execute(cmd, source_gadget.project)
            return True

        return False

    def _execute_create(self, location, adaptor, target_gadget):
        """
        Execute the create-append or create-extend command.

        @param location: the drop location
        @type location: dnd constant
        @param adaptor: adaptor for creating the class
        @type adaptor: L{gazpacho.widgetadaptor.WidgetAdaptor}
        @param target_gadget: the gadget where the drop occurred
        @type target_gadget: L{gazpacho.gadget.Gadget}

        @return: True if the drop was successful
        @rtype: bool
        """
        project = target_gadget.project
        success = False

        if self._is_extend_action(location):
            gadget = Gadget(adaptor, project)
            gadget.create_widget(interactive=True)
            cmd = CreateExtendCommand(gadget, target_gadget, location)
            command_manager.execute(cmd, project)

            success = True

        elif self._is_append_action(location):
            pos = self._get_append_position(target_gadget.widget, location)
            parent = target_gadget.get_parent()
            gadget = Gadget(adaptor, project)
            gadget.create_widget(interactive=True)
            cmd = CreateAppendCommand(gadget, parent, pos)
            command_manager.execute(cmd, project)

            success = True

        if success:
            from gazpacho.palette import palette
            if not palette.persistent_mode:
                palette.unselect_widget()

        return success

    #
    # Signal handlers for the drag source
    #

    def _on_widget__drag_begin(self, event_widget, drag_context):
        """
        Set a drag icon that matches the source widget.
        """
        source_gadget = Gadget.from_widget(event_widget).dnd_gadget
        if source_gadget:
            pixbuf = source_gadget.adaptor.icon.get_pixbuf()
            event_widget.drag_source_set_icon_pixbuf(pixbuf)

    def _on_widget__drag_data_get(self, event_widget, drag_context,
                                  selection_data, info, time):
        """Make the widget data available in the format that was
        requested.

        If the drag and drop occurs within the application the widget
        can be accessed directly otherwise it has to be passed as an
        XML string.
        """
        source_gadget = Gadget.from_widget(event_widget).dnd_gadget

        # If we can't get the widget we indicate this failure by
        # passing an empty string. Not sure if it's correct but it
        # works for us. Note that the source widget is sometimes
        # different from the dragged widget.
        data = ""
        if source_gadget:
            # The widget should be passed as XML
            if info == INFO_TYPE_XML:
                data = source_gadget.to_xml(skip_external_references=True)
            # The widget can be retrieved directly and we only pass the name
            elif info == INFO_TYPE_WIDGET:
                data = source_gadget.name

        selection_data.set(selection_data.target, 8, data)

    #
    # Signal handlers for the drag target
    #

    def _on_widget__drag_data_received(self, event_widget, drag_context,
                                       x, y, data, info, time):
        """
        The data has been received and the appropriate command can now
        be executed.

        If the drag/drop is in the same project the target handles
        everything. If it's between different projects the target only
        handles the drop (paste) and the source takes care of the drag
        (cut).
        """
        # XXX should we validate the drop-zone again? There are
        #     problems with gtk.Entry for some reason and events seem
        #     to slip through. Click on the text entry and drag onto
        #     the text entry (at the end).
        if not self._is_valid_drop_zone(drag_context, event_widget, x, y):
            # XXX this seems to solve the problem but can it be fixed
            #     in a better way? We still get the incorrect cursor.
            drag_context.finish(False, False, time)
            return
        
        # If there is no data we indicate that the drop was not successful
        success = False
        if data.data:
            target_widget, tx, ty = self._get_target_widget(event_widget, x, y)
            project = self._get_target_project(target_widget)
            location = self._get_drop_location(target_widget, tx, ty)[0]
            target_gadget = Gadget.from_widget(target_widget)

            if info in (INFO_TYPE_WIDGET, INFO_TYPE_XML):
                source_gadget = self._get_source_gadget(data, info,
                                                        drag_context, project)
                keep_source = (drag_context.action != gtk.gdk.ACTION_MOVE)
                success = self._execute_drag(location, source_gadget,
                                             target_gadget, keep_source)

            elif info == INFO_TYPE_PALETTE:
                adaptor = project.get_app().add_class
                if adaptor:
                    success = self._execute_create(location, adaptor,
                                                   target_gadget)
                else:
                    success = False

        drag_context.finish(success, False, time)

class PlaceholderDnDHandler(DnDHandler):

    def _get_target_project(self, widget):
        """
        Get the project to which the target belongs.

        @param widget: the target placeholder
        @type widget: L{gazpacho.placeholder.Placeholder}
        """
        return widget.get_project()

    def _set_drag_highlight(self, event_widget, x, y):
        """
        Highlight the widget in an appropriate way to indicate
        that this is a valid drop zone.

        @param event_widget: the target event widget
        @type event_widget: gtk.Widget
        @param x: the mouse x position
        @type x: int
        @param y: the mouse y position
        @type y: int
        """
        event_widget.drag_highlight()

    def _clear_drag_highlight(self, event_widget):
        """
        Clear the drag highligt.

        @param event_widget: the target event widget
        @type event_widget: gtk.Widget
        """
        event_widget.drag_unhighlight()

    def _execute_drag(self, source_gadget, placeholder, keep_source, project):
        """
        Execute the drag and drop command.

        @param source_gadget: the gadget that is being dragged
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param placeholder: the placeholder where the drop occurred
        @type placeholder: L{gazpacho.placeholder.Placeholder}
        @param keep_source: True if the source widget should not be removed
        @type keep_source: bool
        @param project: the target project
        @type project: L{gazpacho.project.Project}

        @return: True if the drop was successful
        @rtype: bool
        """
        if not source_gadget:
            return False

        if keep_source:
            cmd = CommandCutPaste(source_gadget.copy(project), project, placeholder,
                                  False)
        else:
            cmd = CommandDragDrop(source_gadget, placeholder)

        command_manager.execute(cmd, project)
        return True

    #
    # Signal handlers for the drag target
    #

    def _on_widget__drag_data_received(self, event_widget, drag_context,
                                       x, y, data, info, time):
        """
        The data has been received and the appropriate command can now
        be executed.

        If the drag/drop is in the same project the target handles
        everything. If it's between different projects the target only
        handles the drop (paste) and the source takes care of the drag
        (cut).
        """
        # If there is no data we indicate that the drop was not
        # successful
        if not data.data:
            drag_context.finish(False, False, time)
            return

        project = self._get_target_project(event_widget)

        success = False
        if info in (INFO_TYPE_WIDGET, INFO_TYPE_XML):
            # note that the dragged widget isn't always the same as
            # the source widget in the event
            source_gadget = self._get_source_gadget(data, info, drag_context,
                                                    project)
            keep_source = drag_context.action != gtk.gdk.ACTION_MOVE
            
            success = self._execute_drag(source_gadget, event_widget,
                                         keep_source, project)
        elif info == INFO_TYPE_PALETTE:
            gapi.create_gadget(project, project.get_app().add_class,
                               event_widget)
            success = True

        drag_context.finish(success, False, time)


class CommandDragDrop(Command):
    """Command for executing a drag and drop action. This will move
    the widget and cannot be used to drag widgets between programs.
    """

    def __init__(self, source_gadget, target_placeholder):
        """
        Initialize the command.

        @param source_gadget: the source gadget
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param target_placeholder: the target placeholder
        @type target_placeholder: L{gazpacho.placeholder.Placeholder}
        """
        description = _("Drag and Drop widget %s") % source_gadget.name
        Command.__init__(self, description)

        self._undo = False
        self._source_placeholder = None
        self._target_placeholder = target_placeholder
        self._source = source_gadget

    def execute(self):
        if self._undo:
            self._remove_gadget(self._source, self._target_placeholder)
            self._add_gadget(self._source, self._source_placeholder)

        else:
            # Delay the construction of the placeholder until we need it
            if not self._source_placeholder:
                self._source_placeholder = Placeholder()

            self._remove_gadget(self._source, self._source_placeholder)
            self._add_gadget(self._source, self._target_placeholder)

        self._undo = not self._undo

    def _remove_gadget(self, gadget, placeholder):
        """
        Remove the widget from the gadget and replace it with a
        new placeholder.

        @param gadget: the gadget that should be removed
        @type gadget: L{gazpacho.gadget.Gadget}
        @param placeholder: the new placeholder
        @type placeholder: L{gazpacho.placeholder.Placeholder}
        """
        parent = gadget.get_parent()
        Gadget.replace(gadget.widget, placeholder, parent)

        gadget.widget.hide()
        gadget.project.remove_widget(gadget.widget)

    def _add_gadget(self, gadget, placeholder):
        """
        Remove the old placeholder and add a widget from the gadget.

        @param gadget: the gadget that should be added
        @type gadget: L{gazpacho.gadget.Gadget}
        @param placeholder: the old placeholder
        @type placeholder: L{gazpacho.placeholder.Placeholder}
        """
        parent = util.get_parent(placeholder)
        project = parent.project
        Gadget.replace(placeholder, gadget.widget, parent)

        project.add_widget(gadget.widget)
        gadget.select()

        gadget.widget.show_all()
