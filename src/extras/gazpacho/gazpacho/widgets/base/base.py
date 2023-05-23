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
import gobject

from gazpacho import util
from gazpacho.placeholder import Placeholder
from gazpacho.properties import prop_registry, CustomProperty, \
     StringType, TransparentProperty, BooleanType, IntType
from gazpacho.gadget import Gadget
from gazpacho.widgetregistry import widget_registry
from gazpacho.widgetadaptor import WidgetAdaptor

# this ones won't be imported at startup if we don't import it manually
from gazpacho.widgets.base import image
from gazpacho.widgets.base import spinbutton
# pyflakes
assert image and spinbutton

# GtkWidget
class EventsProp(TransparentProperty):
    default = None
prop_registry.override_simple('GtkWidget::events',  EventsProp)

prop_registry.override_simple('GtkWidget::width-request',
                              minimum=-1, maximum=10000)
prop_registry.override_simple('GtkWidget::height-request',
                              minimum=-1, maximum=10000)

class TooltipProp(TransparentProperty):
    def get(self):
        data = gtk.tooltips_data_get(self.object)
        if data is not None:
            return data[2]

    def set(self, value):
        tooltips = self._project.tooltips
        if not tooltips:
            value = None

        tooltips.set_tip(self.object, value, None)
prop_registry.override_property('GtkWidget::tooltip', TooltipProp)

class ObjectDataProp(CustomProperty):
    # name of qdata
    qdata = None
    def get(self):
        value = self.object.get_data(self.qdata)
        # If it is not set (eg None), set the value from the property
        if value is None:
            value = self.object.get_property(self.name)
            self.set(value)

        return value

    def set(self, value):
        self.object.set_data(self.qdata, value)
        self.notify()

class VisibleProp(ObjectDataProp, BooleanType):
    qdata = 'gazpacho::visible'

prop_registry.override_simple('GtkWidget::visible', VisibleProp)
prop_registry.override_simple('GtkWidget::is-focus', ObjectDataProp,
                              qdata='gazpacho::is-focus')

# We don't want has-focus to be editable, what we want to be used
# is is-focus instead.
prop_registry.override_simple('GtkWidget::has-focus', editable=False,
                              persistent=False)

prop_registry.override_simple('GtkWidget::name', translatable=False,
                              priority=0)

class SizeGroupProp(CustomProperty, StringType):
    # we can remove this class when depending in gtk 2.8 since this property
    # is readable there
    editable = True
    translatable = False
    custom = True

    def __init__(self, object):
        super(SizeGroupProp, self).__init__(object)

    def get(self):
        return self.object.get_data('gazpacho::sizegroup')

    def set(self, value):
        self.object.set_data('gazpacho::sizegroup', value)
        self.notify()

    def save(self):
        # gtkbuilder does not use this fake property
        if self._project.get_version() == 'gtkbuilder':
            return None
        return self.get() or None

prop_registry.override_property('GtkWidget::sizegroup', SizeGroupProp)

# FIXME: should be for *all* widgets, but only the onces
#        which has GtkDialog as a parent.
class ResponseIdProp(CustomProperty, IntType):
    editable = True
    translatable = False
    custom = True
    label = "Dialog response"

    def __init__(self, object):
        super(ResponseIdProp, self).__init__(object)

    def get(self):
        return self.object.get_data('gazpacho::response-id')

    def set(self, value):
        self.object.set_data('gazpacho::response-id', value)
        self.notify()

    def save(self):
        if self._project.get_version() == 'gtkbuilder':
            return None
        return super(ResponseIdProp, self).save()
prop_registry.override_property('GtkWidget::response-id', ResponseIdProp)

# GtkContainer
prop_registry.override_simple('GtkContainer::border-width',
                              minimum=0, maximum=10000)
prop_registry.override_simple('GtkContainer::resize-mode',
                              editable=False)

class ContainerAdaptor(WidgetAdaptor):
    def get_children(self, context, widget):
        children = []
        if isinstance(widget, gtk.Container):
            children += util.get_all_children(widget)
        return children

    def replace_child(self, context, current, new, container):
        if current is None:
            container.add(new)
            return

        if current.parent != container:
            return

        props = {}
        for pspec in gtk.container_class_list_child_properties(container):
            props[pspec.name] = container.child_get_property(current,
                                                             pspec.name)

        gtk.Container.remove(container, current)
        container.add(new)

        for name, value in list(props.items()):
            container.child_set_property(new, name, value)

    def fill_empty(self, context, widget):
        widget.add(Placeholder())

# GtkMisc
align_ns = dict(default=0.5, minimum=0.0, maximum=1.0,
                step_increment=0.01, page_increment=0.1,
                climb_rate=0.2)
prop_registry.override_simple('GtkMisc::xalign', **align_ns)
prop_registry.override_simple('GtkMisc::yalign', **align_ns)

# GtkPaned
class PanedAdaptor(ContainerAdaptor):
    def fill_empty(self, context, paned):
        paned.add1(Placeholder())
        paned.add2(Placeholder())
        # we want to set the position in the middle but
        # as the paned has not yet a parent it is not
        # realized we can't know its size
        gobject.idle_add(self._set_position, paned)

    def _set_position(self, paned):
        """This function get called until the paned is realized.
        Then it puts the bar in the middle.
        """
        if paned.flags() & gtk.REALIZED:
            alloc = paned.get_allocation()
            if isinstance(paned, gtk.VPaned):
                pos = alloc.height / 2
            else:
                pos = alloc.width / 2
            paned.set_position(pos)
            return False
        else:
            return True

# GtkScrolledWindow
# these widgets does not need a viewport when added to a scrolledwindow
scrollable_widgets = (gtk.TreeView, gtk.TextView, gtk.Viewport)

class ScrolledWindowAdaptor(ContainerAdaptor):

    def fill_empty(self, context, scrolledwindow):
        self._add_viewport(scrolledwindow, context.get_project())

    def _add_viewport(self, scrolledwindow, project):
        """ScrolledWindow should be empty before calling this method"""
        klass = widget_registry.get_by_name('GtkViewport')
        viewport = Gadget(klass, project)
        viewport.create_widget(interactive=False)
        scrolledwindow.add(viewport.widget)
        project.add_widget(viewport.widget)
        viewport.widget.show_all()
        return viewport

    def replace_child(self, context, current, new, container):
        global scrollable_widgets

        if current is None:
            raise ValueError("Can not replace None widget")

        # we don't care about current since it is probably different from
        # our child because we always have a viewport when adding a widget
        # that is not scrollable
        child = container.get_child()
        container.remove(child)
        project = context.get_project()
        if child is not current:
            project.remove_widget(child)

        # luckily viewports or scrolledwindow does not have any packing
        # properties

        if isinstance(new, scrollable_widgets):
            container.add(new)
        elif isinstance(new, Placeholder):
            self._add_viewport(container, project)
        else:
            raise ValueError("You can only put scrollable widgets or "
                             "placeholders inside a ScrollableWindow: "
                             "%s" % new)

# GtkViewport
class ViewportAdaptor(ContainerAdaptor):

    def replace_child(self, context, current, new, container):
        """If the new child is a scrollable widget and our parent is a
        scrolled window, we remove ourselves"""
        global scrollable_widgets
        parent = container.get_parent()
        if (isinstance(parent, gtk.ScrolledWindow)
            and isinstance(new, scrollable_widgets)):
            project = context.get_project()
            project.remove_widget(container)
            parent.remove(container)
            parent.add(new)
        else:
            ContainerAdaptor.replace_child(self, context, current, new,
                                           container)

class IconViewAdaptor(ContainerAdaptor):
    def fill_empty(self, context, widget):
        pass

# GtkLabel
class LabelAdaptor(WidgetAdaptor):
    def post_create(self, context, label, interactive):
        label.set_label(label.get_name())
        label.set_alignment(0.0, 0.5)

prop_registry.override_simple('GtkLabel::mnemonic-widget', editable=True)
prop_registry.override_simple('GtkLabel::label', priority=1)

# GtkFrame
class FrameAdaptor(ContainerAdaptor):
    def post_create(self, context, frame, interactive):
        frame.set_label(frame.get_name())
        frame.set_shadow_type(gtk.SHADOW_NONE)

prop_registry.override_simple('GtkFrame::label', default="Frame")
prop_registry.override_simple('GtkFrame::label-xalign', **align_ns)
prop_registry.override_simple('GtkFrame::label-yalign', **align_ns)

# GtkExpander
class ExpanderAdaptor(ContainerAdaptor):
    def post_create(self, context, expander, interactive):
        expander.set_label(expander.get_name())
        expander.set_expanded(True)

prop_registry.override_simple('GtkExpander::expanded', default=True)

# GtkEntry
# optional="True" optional-default="False" ?
prop_registry.override_simple('GtkEntry::width-chars', default=0)

# GtkProgressBar
# Gtk+ is broken here
p = prop_registry.get_prop_type('GtkProgressBar', 'activity-step')
# epydoc
if p is not None:
    p.minimum == 0 # HACK

# default child properties, not quite implemented
#prop_registry.override_simple('GtkLabel::expand', parent='GtkVBox',
#                              default=False)
#prop_registry.override_simple('GtkMenubar::expand', parent='GtkVBox',
#                              default=False)
#prop_registry.override_simple('GtkStatusbar::expand', parent='GtkVBox',
#                              default=False)
#prop_registry.override_simple('GtkToolbar::expand', parent='GtkVBox',
#                              default=False)
#prop_registry.override_simple('GtkVSeparator::expand', parent='GtkHBox',
#                              default=False)



