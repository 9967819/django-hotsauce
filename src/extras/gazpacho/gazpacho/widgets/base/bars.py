# Copyright (C) 2005 by SICEm S.L. and Async Open Source
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
from xml.dom import minidom

import gtk

from gazpacho.propertyeditor import PropertyCustomEditorWithDialog
from gazpacho.i18n import _
from gazpacho.properties import prop_registry, TransparentProperty, StringType
from gazpacho.uieditor import UIEditor
from gazpacho.gadget import Gadget
from gazpacho.gaction import GActionGroup
from gazpacho.widgets.base.base import ContainerAdaptor
from gazpacho.placeholder import Placeholder

class UIPropEditor(PropertyCustomEditorWithDialog):
    dialog_class = UIEditor
    button_text = _('Edit UI Definition...')

class UIAdaptor(TransparentProperty, StringType):
    """This represents a fake property to edit the ui definitions of
    menubars and toolbars.

    It does not store anything because this information is stored in
    the uimanager itself. It's just a way to put a button in the Gazpacho
    interface to call the UIEditor.
    """
    custom_editor = UIPropEditor

class MenuBarUIAdapter(UIAdaptor):
    pass

#prop_registry.override_property('GtkMenuBar::ui', MenuBarUIAdapter)

class ToolbarUIAdapter(UIAdaptor):
    pass

prop_registry.override_property('GtkToolbar::ui', ToolbarUIAdapter)

class CommonBarsAdaptor(ContainerAdaptor):

    def post_create(self, context, widget, ui_string):
        # create some default actions
        gadget = Gadget.from_widget(widget)
        project = gadget.project

        # create default action group if it doesn't exist
        project = context.get_project()
        if project.uim.get_action_group('DefaultActions') is None:
            project.add_action_group(GActionGroup('DefaultActions'))

        project.uim.add_ui(gadget, ui_string)
        new_widget = project.uim.get_widget(gadget)

        # we need to replace widget with new_widget
        gadget.setup_widget(new_widget)
        #gadget.apply_properties()

    def save(self, context, gadget):
        """This saver is needed to avoid saving the children of toolbars
        and menubars
        """

        project = context.get_project()
        if project.get_version() == 'gtkbuilder':
            constructor = project.uim.get_name()
        else:
            constructor = 'initial-state'
        gadget.constructor = constructor

    def load(self, context, widget):
        """This loader is special because of these features:
        - It does not load the children of the menubar/toolbar
        - Load the uimanager and put its content (action groups) into the
        project
        """

#         # we need to save the properties of this widget because otherwise
#         # when we got it from the uimanager it's gonna be another widget with
#         # different properties
#         props = {}
#         for prop in gobject.list_properties(widget):
#             if 1 or prop.flags != gobject.PARAM_READWRITE:
#                 continue
#             if propertyclass.get_type_from_spec(prop) is gobject.TYPE_OBJECT:
#                 continue
#             # FIXME: This need to use the values from the catalog.
#             # But it doesn't work right now, the property in
#             # klass.properties is always set to False.
#             if prop.name == 'parent' or prop.name == 'child':
#                 continue
#             props[prop.name] = widget.get_property(prop.name)

        project = context.get_project()

        old_name = widget.name
        gadget = Gadget.load(widget, project)
        gadget._name = gadget.widget.name

        # change the widget for the one we get from the uimanager
        project.uim.load_widget(gadget, old_name)

        return gadget

    def fill_empty(self, context, widget):
        pass

    def delete(self, context, widget):
        gadget = Gadget.from_widget(widget)
    
        # replace the widget with a placeholder
        parent = gadget.get_parent()
        placeholder = None
        if parent:
            # since the uim widget will be removed we have to replace
            # it with a placeholder in order to know it's location
            placeholder = Placeholder()
            placeholder.set_name(gadget.name)
            Gadget.replace(gadget.widget, placeholder , parent)
        
        uim = context.get_project().uim
        ui_defs = uim.get_ui(gadget)
        uim.remove_gadget(gadget)
    
        if placeholder:
            # the placeholder has to be associated with the gadget,
            # this is a bit ugly
            gadget.widget = placeholder
            placeholder.set_data('gazpacho::gadget', gadget)
    
        return ui_defs, placeholder
    
    def restore(self, context, widget, data):
        ui_defs, placeholder = data    
        gadget = Gadget.from_widget(widget)
        
        # adding the widget to uim will replace the gtk-widget
        # connected to the gadget
        context.get_project().uim.add_gadget(gadget, ui_defs)
    
        if placeholder:
            # replace the placeholder with the real uim widget
            Gadget.replace(placeholder, gadget.widget, gadget.get_parent())
        


from gazpacho.widgets.base.menueditor.widgets import MenuBar

class MenuBarEditingInfo(object):
    def __init__(self):
        self.editing = False
        self.edit_activate_id = 0
        self.fakeBar = None

class MenuBarAdaptor(ContainerAdaptor):
    """Adaptor that allow in-place editing of MenuBars

    The basic idea of this adaptor is to put an 'Edit' button in each
    menu bar. When the user clicks on this button the menubar is replaced
    by a custom widget that looks like a menubar but it is not. It's a
    menueditor.widgets.MenuBar widget that allow in-place edition of a
    menubar.

    When the user selects another widget of the project the fake menubar
    is replaced again by the real one.
    """

    def __init__(self, *args, **kwargs):
        super(MenuBarAdaptor, self).__init__(*args, **kwargs)
        self._bars = {}

    def post_create(self, context, menuBar, interactive):
        # create default action group if it doesn't exist
        project = context.get_project()
        if project.uim.get_action_group('DefaultActions') is None:
            project.add_action_group(GActionGroup('DefaultActions'))

        # Add the basic UI definition
        gadget = Gadget.from_widget(menuBar)
        name = gadget.name
        ui_string = '<menubar action="%s" name="%s"/>' % (name, name)
        project.uim.add_ui(gadget, ui_string)
        new_widget = project.uim.get_widget(gadget)
        self._add_edit_button(new_widget)

        # we need to replace widget with new_widget
        gadget.setup_widget(new_widget)

        self._bars[new_widget] = MenuBarEditingInfo()

    def fill_empty(self, context, widget):
        pass

    def _add_edit_button(self, widget):
        item = gtk.ImageMenuItem(stock_id=gtk.STOCK_EDIT)
        item.set_right_justified(True)
        item.show_all()
        widget.append(item)
        item.connect('button-press-event', self._on_edit_press_event, widget)

    def _on_edit_press_event(self, item, event, menuBar):
        self._start_editing(menuBar)

    def _start_editing(self, menuBar):
        gadget = Gadget.from_widget(menuBar)
        project = gadget.project

        # create the fake menubar
        fakeBar = MenuBar(gadget)

        # load it with our xml ui definition
        ui_def = project.uim.get_ui(gadget, 'initial-state')
        if ui_def:
            doc = minidom.parseString(ui_def[0])
            fakeBar.load(doc.documentElement)

        # replace the real one with this fake one
        fakeBar.show_all()
        self.replace_child(project.context, menuBar, fakeBar, menuBar.parent)

        # save some information to restore the state in _end_editing
        self._bars[menuBar].editing = True
        self._bars[menuBar].fakeBar = fakeBar
        i = project.selection.connect('selection-changed',
                                      self._on_selection__changed, menuBar)
        self._bars[menuBar].edit_activate_id = i

        fakeBar.get_toplevel().queue_draw()

    def _end_editing(self, menuBar):
        gadget = Gadget.from_widget(menuBar)
        if not gadget:
            return
        project = gadget.project
        fakeBar = self._bars[menuBar].fakeBar
        parent = fakeBar.parent

        # put the real menuBar back in its place
        newBar = project.uim.get_widget(gadget)
        fakeBar.hide_all() # it's very important to hide this widget now
        newBar.show_all()
        self.replace_child(project.context, fakeBar, newBar, parent)

        # restore the state
        i = self._bars[menuBar].edit_activate_id
        project.selection.disconnect(i)
        self._bars[menuBar].editing = False
        self._bars[menuBar].fakeBar = None
        self._bars[menuBar].edit_activate_id = 0

        if newBar != menuBar:
            self._add_edit_button(newBar)
            project.remove_widget(menuBar)
            gadget.setup_widget(newBar)
            project.add_widget(newBar)

            info = self._bars[menuBar]
            del self._bars[menuBar]
            self._bars[newBar] = info
            menuBar.destroy()

    def _on_selection__changed(self, selection, menuBar):
        is_editing = self._bars[menuBar].editing
        found = False
        for widget in selection:
            if widget == menuBar:
                found = True
                break

        if not found and is_editing:
            self._end_editing(menuBar)

    # The save and load methods are taken from the CommonsBarAdaptor
    # They should be refactored again when we change the Toolbar adaptor
    def save(self, context, gadget):
        """This saver is needed to avoid saving the children of toolbars
        and menubars
        """

        project = context.get_project()
        if project.get_version() == 'gtkbuilder':
            constructor = project.uim.get_name()
        else:
            constructor = 'initial-state'
        gadget.constructor = constructor

    def load(self, context, widget):
        """This loader is special because of these features:
        - It does not load the children of the menubar/toolbar
        - Load the uimanager and put its content (action groups) into the
        project
        """

#         # we need to save the properties of this widget because otherwise
#         # when we got it from the uimanager it's gonna be another widget with
#         # different properties
#         props = {}
#         for prop in gobject.list_properties(widget):
#             if 1 or prop.flags != gobject.PARAM_READWRITE:
#                 continue
#             if propertyclass.get_type_from_spec(prop) is gobject.TYPE_OBJECT:
#                 continue
#             # FIXME: This need to use the values from the catalog.
#             # But it doesn't work right now, the property in
#             # klass.properties is always set to False.
#             if prop.name == 'parent' or prop.name == 'child':
#                 continue
#             props[prop.name] = widget.get_property(prop.name)

        project = context.get_project()

        old_name = widget.name
        gadget = Gadget.load(widget, project)
        gadget._name = gadget.widget.name

        # change the widget for the one we get from the uimanager
        project.uim.load_widget(gadget, old_name)

        # add the edit button
        self._add_edit_button(gadget.widget)

        # add it to our bars dictionary
        if gadget.widget not in list(self._bars.keys()):
            self._bars[gadget.widget] = MenuBarEditingInfo()

        return gadget

    # XXX this is the same as for toolbar and should be in a common base class

    def delete(self, context, widget):
        gadget = Gadget.from_widget(widget)
    
        # replace the widget with a placeholder
        parent = gadget.get_parent()
        placeholder = None
        if parent:
            placeholder = Placeholder()
            placeholder.set_name(gadget.name)
            Gadget.replace(gadget.widget, placeholder , parent)
        
        uim = context.get_project().uim
        ui_defs = uim.get_ui(gadget)
        uim.remove_gadget(gadget)
    
        if placeholder:
            gadget.widget = placeholder
            placeholder.set_data('gazpacho::gadget', gadget)
    
        return ui_defs, placeholder
    
    def restore(self, context, widget, data):
        ui_defs, placeholder = data    
        gadget = Gadget.from_widget(widget)
        
        # adding the widget to uim will replace the gtk-widget
        # connected to the gadget
        context.get_project().uim.add_gadget(gadget, ui_defs)
    
        if placeholder:
            Gadget.replace(placeholder, gadget.widget, gadget.get_parent())


class ToolbarAdaptor(CommonBarsAdaptor):
    def post_create(self, context, toolbar, interactive=True):
        gadget = Gadget.from_widget(toolbar)
        ui_string = '<toolbar action="%s" name="%s"/>' % (gadget.name,
                                                          gadget.name)

        super(ToolbarAdaptor, self).post_create(context, toolbar, ui_string)

