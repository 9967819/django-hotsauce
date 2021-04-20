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

import gobject
import gtk
from gtk import gdk
from kiwi.component import get_utility
from kiwi.utils import gsignal, type_register

from gazpacho.app.bars import bar_manager
from gazpacho.annotator import Annotator, draw_annotations
from gazpacho.commandmanager import command_manager
from gazpacho.interfaces import IGazpachoApp
from gazpacho.popup import Popup
from gazpacho.placeholder import Placeholder
from gazpacho.properties import prop_registry
from gazpacho.referencecontainer import ReferenceContainer
from gazpacho.util import get_parent, get_all_children
from gazpacho.widgetregistry import widget_registry

def load_gadget_from_widget(widget, project):
    """  This function creates a gadget from a widget.
    It recursively creates any children of the original widget.
    This method is mainly used when loading a .glade file with
    gazpacho.loader

    Also makes sure the name of the widget is unique in the project
    parameter and if not, change it for a valid one.

    @return: a new gadget
    @rtype: Gadget
    """

    # widget may not have a name if it is an intermediate internal children
    # For example, the label of a button does not have a name
    if widget.name is None:
        # this is not an important widget but maybe its children are
        if isinstance(widget, gtk.Container):
            for child in get_all_children(widget):
                load_gadget_from_widget(child, project)
        return

    type_name = gobject.type_name(widget)
    adaptor = widget_registry.get_by_name(type_name)
    if adaptor is None:
        print('Warning: could not get the class from widget: %s' % widget)
        return

    gadget = adaptor.load(project.context, widget)
    if not isinstance(gadget, Gadget):
        raise TypeError("WidgetAdaptor.load should always return a Gadget"
                        " not %s" % gadget)
    if not gobject.type_is_a(gadget.widget, adaptor.type):
        raise TypeError("%s is not of the type %s"
                        % (gadget.widget, adaptor.type))
    return gadget

# XXX: Rename to Gadget
class BaseGadget(gobject.GObject):
    """
    This is essentially a wrapper around regular widget with more data and
    functionality needed for Gazpacho.

    It has access to the widget it is associated with, the Project it
    belongs to and the instance of its WidgetAdaptor.

    Given a widget you can ask which Gadget is associated with it
    using the get_from_widget function or, if no one has been created yet you
    can create one with the create_from_widget method.

    A gadget has a signal dictionary where the keys are signal names and the
    values are lists of signal handler names. There are methods to
    add/remove/edit these.

    It store all the properties (wrappers for gobject properties) and you can
    get any of them with get_prop. It knows how to handle normal
    properties and packing properties.

    @ivar internal_name: name of internal widget or None
    @ivar adaptor: widget adaptor we belong to
    @ivar project: project tied to gadget
    @ivar widget: widget associated with this gadget
    @ivar constructor: cConstructor, used by UIManager
    @ivar maintain_gtk_properties:
      flag that tells the property code if this widget should keep the
      values of its properties when creating the GazpachoProperties or not
    @ivar references: a reference container for keeping track of which
      objects are refering to this gadget
    """
    gsignal('add-signal', object)
    gsignal('remove-signal', object)

    def __init__(self, adaptor, project):
        """This init method is not complete because there are several scenarios
        where widgets are created:

            - Normal creation in Gazpacho
            - When loading from a .glade file
            - When copying from another gadget
            - Internal gadgets

        So you should call the appropiate method after this basic initialization.
        """
        gobject.GObject.__init__(self)
        self._signals = {} # name -> handlers
        self._deleted_data = None
        self._deleted = False
        self.properties = {}
        self.child_properties = {}

        self.adaptor = adaptor
        self.constructor = None
        self.maintain_gtk_properties = False
        self.internal_name = None
        self.project = project
        # XXX: Rename
        self.widget = None

        self.references = ReferenceContainer(self)

    # XXX: Generalize name

    def __repr__(self):
        if self.widget:
            name = self.widget.name
        else:
            name = '(empty)'
        return '<%s %s>' % (self.__class__.__name__, name)

    # Properties

    def _get_name(self):
        return self.widget.name

    def _set_name(self, value):
        # set_name calls notify::name
        self.widget.set_name(value)

    name = property(_get_name, _set_name)


    def _get_deleted(self):
        return self._deleted

    def _set_deleted(self, deleted):
        if self._deleted == deleted:
            return
        
        self._deleted = deleted

        if not deleted:
            self.adaptor.restore(self.project.context, self.widget, self._deleted_data)
            self._deleted_data = None
            self.references.restore_references()

        # We need to update all children as well
        for child_widget in self.get_children():
            child_gadget = Gadget.from_widget(child_widget)
            if child_gadget:
                child_gadget.deleted = deleted

        if deleted:
            self.references.clear_references()
            self._deleted_data = self.adaptor.delete(self.project.context, self.widget)

    deleted = property(_get_deleted, _set_deleted)

    # Class methods

    #@classmethod
    def load(cls, widget, project):
        """Helper function of load_gadget_from_widget. Create the Gazpacho
        widget and create a right name for it
        """
        assert project != None

        adaptor = widget_registry.get_by_type(widget)
        assert adaptor != None, widget

        gadget = cls(adaptor, project)
        gadget.setup_widget(widget)

        gadget.internal_name = widget.get_data(
            'gazpacho::internal-child-name')

        return gadget
    load = classmethod(load)

    #@classmethod
    def from_xml(cls, project, xml, name=None):
        """
        Creates a new gadget from xml.

        @param project: project
        @param xml: xml string
        @param name: name of widget or None
        """

        from gazpacho.project import GazpachoObjectBuilder
        wt = GazpachoObjectBuilder(buffer=xml, placeholder=Placeholder,
                                   app=project.get_app())
        project.uim.load(wt)

        # Load models before widgets
        models = [w for w in wt.toplevels if isinstance(w, gtk.ListStore)]
        for model in models:
            project.model_manager.load_model(model)

        if name:
            widget = wt.get_widget(name)
        else:
            widgets = wt.get_widgets()
            if len(widgets) > 1:
                raise AssertionError(
                    "should only be one widget: found %r" % widgets)
            widget = widgets[0]
        return load_gadget_from_widget(widget, project)
    from_xml = classmethod(from_xml)

    #@classmethod
    def replace(cls, old_widget, new_widget, parent):
        # FIXME: MESS MESS MESS
        new_gadget = cls.from_widget(new_widget)
        old_gadget = old_widget and cls.from_widget(old_widget)

        new_widget = new_gadget and new_gadget.widget or new_widget
        old_widget = old_gadget and old_gadget.widget or old_widget

        if parent is None:
            parent = get_parent(old_widget)

        parent.adaptor.replace_child(parent.project.context,
                                     old_widget,
                                     new_widget,
                                     parent.widget)
        return new_gadget
    replace = classmethod(replace)

    #@classmethod
    def from_widget(cls, widget):
        return widget.get_data('gazpacho::gadget')
    from_widget = classmethod(from_widget)

    # Public

    def get_children(self):
        """
        Get a list of children for the gadget.
        Note that an adaptor can override the behavior so this
        should be used instead of widget.get_children() directly
        @returns: list of children
        """
        return self.adaptor.get_children(self.project.context,
                                         self.widget)

    def get_prop(self, prop_name):
        return self._internal_get_prop(prop_name, child=False)

    def get_child_prop(self, prop_name):
        return self._internal_get_prop(prop_name, child=True)

    def setup_internal_widget(self, widget, internal_name, parent_name):
        self.internal_name = internal_name
        widget.set_name(parent_name + '-' + internal_name)

        self.setup_widget(widget)

    def setup_widget(self, widget):
        if self.widget is not None:
            self.widget.set_data('gazpacho::gadget', None)
            self.widget = None

        self.widget = widget
        self.constructor = widget.get_data('gazpacho::uimanager-name')
        self.widget.set_data('gazpacho::gadget', self)

    def create_widget(self, interactive=True):
        """Second part of the init process when creating a widget in
        the usual way.
        If the 'interactive' argument is false no popups will show up to
        ask for options
        """

        # XXX: Clean up this horrible mess
        widget = self.adaptor.create(self.project.context, interactive)
        self.project.set_new_widget_name(widget)
        self.setup_widget(widget)
        self.adaptor.post_create(self.project.context, widget, interactive)
        self.adaptor.fill_empty(self.project.context, widget)

    def copy(self, project=None, keep_name=False):
        """
        Create a copy of the widget. You must specify a project since
        a name conflict resolution will be performed for the copy.

        @param project: project where the source widget
          will live in, if None the project of the gadget will be used.
        @param keep_name: True if the name should not be modified
        """

        if not project:
            project = self.project

        gadget = Gadget.from_xml(project, self.to_xml(), self.name)
        if not keep_name:
            project.set_new_widget_name(gadget.widget)
        return gadget

    def select(self):
        """
        Select this widget, i.e. clear the current selection and add
        the widget.
        """
        self.project.selection.set(self.widget)

    def to_xml(self, skip_external_references=False):
        """
        @returns: an xml representation of the gadget
        """
        from gazpacho.filewriter import XMLWriter
        xw = XMLWriter(project=self.project)
        return xw.serialize(self, skip_external_references)

    def is_toplevel(self):
        """
        @returns: True if the gadget is a toplevel
        """
        return self.adaptor.is_toplevel()

    def add_signal_handler(self, signal_handler):
        """
        Add a signal handler.

        @param signal_handler: the signal handler
        @type signal_handler: L{gazpacho.signaleditor.SignalInfo}
        """
        name = signal_handler.normalized_name
        self._signals.setdefault(name, []).append(signal_handler)
        self.emit('add-signal', signal_handler)

    def remove_signal_handler(self, signal_handler):
        """
        Remove the specified signal handler.

        @param signal_handler: the signal handler
        @type signal_handler: L{gazpacho.signaleditor.SignalInfo}
        """
        name = signal_handler.normalized_name
        if name in self._signals:
            self._signals[name].remove(signal_handler)
            self.emit('remove-signal', signal_handler)

    def change_signal_handler(self, old_signal_handler, new_signal_handler):
        old_name = old_signal_handler.normalized_name
        if old_name != new_signal_handler.normalized_name:
            return

        if not old_name in self._signals:
            return

        signals = self._signals[old_name]
        signals[signals.index(old_signal_handler)] = new_signal_handler.copy()

    def list_signal_handlers(self, signal_name):
        """
        Get a list of all signal handlers for which their normalized
        handler names matches the specified name.

        @param signal_name: the normalized signal handler name
        @type signal_name: str
        @return: a list of signal handler info objects
        @rtype: list (of L{gazpacho.signaleditor.SignalInfo})
        """
        # XXX should we normalize the name?
        return self._signals.get(signal_name, [])

    def get_all_signal_handlers(self):
        return list(self._signals.values())

    # Private

    def _create_prop(self, prop_name, child=False):
        # Get the property type
        type_name = gobject.type_name(self.widget)
        if child:
            parent = self.widget.get_parent()
        else:
            parent = None
        prop_type = prop_registry.get_prop_type(type_name, prop_name, parent)

        # Instantiate the property from the property type
        return prop_type(self)

    def _internal_get_prop(self, prop_name, child):
        if child:
            properties = self.child_properties
        else:
            properties = self.properties
        if prop_name in properties:
            return properties[prop_name]

        prop = self._create_prop(prop_name, child)
        properties[prop_name] = prop
        return prop

type_register(BaseGadget)

# XXX: Rename/Move to WidgetGadget
class Gadget(BaseGadget):
    """
    A wrapper around a gtk.Widget.
    Adds DND handlers and annotations.

    @ivar dnd_gadget: DND the widget that should be dragged
      (not necessarily this one)
    """

    def __init__(self, adaptor, project):
        BaseGadget.__init__(self, adaptor, project)

        self._dnd_drop_region = None
        self.dnd_gadget = None

    # Class methods

    #@classmethod
    def replace(cls, old_widget, new_widget, parent):
        gadget = super(Gadget, cls).replace(old_widget, new_widget, parent)
        if gadget:
            gadget._connect_signal_handlers(gadget.widget)
        return gadget
    replace = classmethod(replace)

    # Public

    def get_parent(self):
        if self.widget.flags() & gtk.TOPLEVEL:
            return None

        return get_parent(self.widget)

    def setup_widget(self, widget):
        BaseGadget.setup_widget(self, widget)

        self.widget.add_events(gdk.BUTTON_PRESS_MASK |
                               gdk.BUTTON_RELEASE_MASK |
                               gdk.KEY_PRESS_MASK |
                               gdk.POINTER_MOTION_MASK)
        if self.widget.flags() & gtk.TOPLEVEL:
            self.widget.connect('delete-event', self._on_widget__delete_event)

        self.widget.connect('popup-menu', self._on_widget__popup_menu)
        self.widget.connect('key-press-event', self._on_widget__key_press_event)

        self._connect_signal_handlers(widget)

        from gazpacho.dndhandlers import WidgetDnDHandler

        dndhandler = WidgetDnDHandler()

        # Init Drag and Drop

        # XXX we need to attach handlers for all widgets even if they
        # do not support dnd themselves (e.g. windows) since they
        # might have to handle the events for their children. This
        # should hopefully be solved in a better way at some point
        dndhandler.connect_drag_handlers(self.widget)
        dndhandler.connect_drop_handlers(self.widget)

    def setup_toplevel(self):
        """Add the action groups of Gazpacho to this toplevel and
        also set this toplevel transient for the main window.
        """
        widget = self.widget
        widget.add_accel_group(bar_manager.get_accel_group())

        # make window management easier by making created windows
        # transient for the editor window
        widget.set_transient_for(get_utility(IGazpachoApp).get_window())

    def set_drop_region(self, region):
        """Set the drop region and make sure it is painted.

        @param region: a tuple of x, y, width and height
        @type region: tuple
        """
        self._dnd_drop_region = region
        self.widget.queue_draw()

    def clear_drop_region(self):
        """Clear the drop region and make sure it is not painted anymore."""
        if self._dnd_drop_region:
            self._dnd_drop_region = None
            self.widget.queue_draw()

    # Private

    def _connect_signal_handlers(self, widget):
        # don't connect handlers for placeholders
        if isinstance(widget, Placeholder):
            return

        widget.set_redraw_on_allocate(True)

        # check if we've already connected an event handler
        if not widget.get_data('event-handler-connected'):
            # we are connecting to the event signal instead of the more
            # apropiated expose-event and button-press-event because some
            # widgets (ComboBox) does not allows us to connect to those
            # signals. See http://bugzilla.gnome.org/show_bug.cgi?id=171125
            # Hopefully we will be able to fix this hack if GTK+ is changed
            # in this case
            widget.connect('event', self._on_widget__event)
            widget.connect('event-after', self._on_widget__event_after)

#            widget.connect("expose-event", self._expose_event)
#            widget.connect("button-press-event", self._button_press_event)
            widget.set_data('event-handler-connected', 1)

        ##
        ## # we also need to get expose events for any children
        ## if isinstance(widget, gtk.Container):
        ##     widget.forall(self._connect_signal_handlers)

    def  _draw_drop_region(self, widget, expose_window, annotator=None):
        if not annotator:
            annotator = Annotator(widget, expose_window)

        color = (0, 0, 1)

        (x, y, width, height) = self._dnd_drop_region

        annotator.draw_border(x, y, width, height, color)

    def _find_deepest_child_at_position(self, toplevel, container, x, y):
        found = None
        if isinstance(container, gtk.Container):
            for widget in get_all_children(container):
                coords = toplevel.translate_coordinates(widget, x, y)
                if len(coords) != 2:
                    continue
                child_x, child_y = coords

                # sometimes the found widget is not mapped or visible
                # think about a widget in a notebook page which is not selected
                if (0 <= child_x < widget.allocation.width and
                    0 <= child_y < widget.allocation.height and
                    widget.flags() & gtk.MAPPED):
                    found = self._find_deepest_child_at_position(toplevel,
                                                                 widget, x, y)
                    if found:
                        break

        return found or Gadget.from_widget(container)

    def _retrieve_from_event(self, base, event):
        """ Returns the widget in x, y of base.
        This is needed because for widgets that does not have a
        GdkWindow the click event goes right to their parent.
        """

        x = int(event.x)
        y = int(event.y)
        window = base.get_toplevel()
        if window.flags() & gtk.TOPLEVEL:
            top_x, top_y = base.translate_coordinates(window, x, y)
            return self._find_deepest_child_at_position(window, window,
                                                        top_x, top_y)

    def _button_press_event(self, widget, event):
        """
        When a widget is clicked it is selected. If it's a right click
        a context menu will be shown. If it is a left click one of
        several actions can take place.

        If the widget is not already selected it will be selected and
        nothing more will happen. If it is selected the event will be
        passed to the actual widget.

        If the Shift modifier is used the widgets will be selected in
        a circular fashion where. the parent of the currently selected
        widget will be selected.

        If the Control modifier is used the widget will be added to or
        removed from the selection.
        """
        gadget = self._retrieve_from_event(widget, event)
        if not gadget:
            return

        # DND store the widget, we might need it later
        self.dnd_gadget = gadget

        widget = gadget.widget
        # Make sure to grab focus, since we may stop default handlers
        if widget.flags() & gtk.CAN_FOCUS:
            widget.grab_focus()

        if event.button == 1:
            if event.type is not gdk.BUTTON_PRESS:
                #only single clicks allowed, thanks
                return False

            # Shift clicking circles through the widget tree by
            # choosing the parent of the currently selected widget.
            if event.state & gdk.SHIFT_MASK:
                self.project.selection.circle(widget)
                return True

            # Control clicking adds or removes the widget from the
            # selection
            if event.state & gtk.gdk.CONTROL_MASK:
                self.project.selection.toggle(widget)
                return True

            # if it's already selected don't stop default handlers,
            # e.g toggle button
            selected = widget in self.project.selection
            self.project.selection.set(widget)
            return not selected
        elif event.button == 3:
            # first select the widget
            self.project.selection.set(widget)

            # then popup the menu
            popup = Popup(command_manager, gadget)
            popup.pop(event)
            return True

        return False

    def _button_release_event(self, widget, event):
        gadget = self._retrieve_from_event(widget, event)
        if not gadget:
            return
        return gadget.adaptor.button_release(gadget.project.context,
                                              gadget.widget, event)

    def _motion_notify_event(self, widget, event):
        gadget = self._retrieve_from_event(widget, event)
        if not gadget:
            return
        return gadget.adaptor.motion_notify(gadget.project.context,
                                             gadget.widget, event)

    def _expose_event_after(self, widget, event):
        draw_annotations(widget, event.window)

        if self._dnd_drop_region:
            self._draw_drop_region(widget, event.window)

    # Callbacks
    def _on_widget__delete_event(self, widget, event):
        return widget.hide_on_delete()

    def _on_widget__event(self, widget, event):
        """We only delegate this call to the appropiate event handler"""
        if event.type == gdk.BUTTON_PRESS:
            return self._button_press_event(widget, event)
        elif event.type == gdk.BUTTON_RELEASE:
            return self._button_release_event(widget, event)
        elif event.type == gdk.MOTION_NOTIFY:
            return self._motion_notify_event(widget, event)

        return False

    def _on_widget__event_after(self, widget, event):
        """We only delegate this call to the appropiate event handler"""
        if event.type == gdk.EXPOSE:
            self._expose_event_after(widget, event)

    def _on_widget__key_press_event(self, widget, event):
        gadget = Gadget.from_widget(widget)

        if event.keyval in (gtk.keysyms.Delete, gtk.keysyms.KP_Delete):
            # We will delete all the selected items
            if len(self.project.selection) == 1:
                gadget.project.delete_selection()
            return True

        return False

    def _on_widget__popup_menu(self, widget):
        return True # XXX TODO

