"""Widgets used to edit menubars

They are very similar to the real GTK+ ones but a) allow in-place edition
of the menubar and b) has less advanced features like multiscreen/monitor
support or keyboard navigation
"""
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
import xml.dom

import gobject
import gtk
import pango

from kiwi.ui.dialogs import error

from gazpacho.actioneditor import CommandAddRemoveAction, CommandEditAction
from gazpacho.commandmanager import command_manager
from gazpacho.gaction import GAction
from gazpacho.i18n import _
from gazpacho.uieditor import CommandUpdateUIDefinitions
from gazpacho.widgets.base.menueditor import contextmenu
from gazpacho.widgets.base.menueditor import gtkutils

MENU_SHELL_TIMEOUT = 500

# Backward compatibility with GTK+ 2.6.X and below
if gtk.gtk_version < (2, 8, 0):
    (PACK_DIRECTION_LTR,
     PACK_DIRECTION_RTL,
     PACK_DIRECTION_TTB,
     PACK_DIRECTION_BTT) = list(range(4))
else:
    PACK_DIRECTION_LTR = gtk.PACK_DIRECTION_LTR
    PACK_DIRECTION_RTL = gtk.PACK_DIRECTION_RTL
    PACK_DIRECTION_TTB = gtk.PACK_DIRECTION_TTB
    PACK_DIRECTION_BTT = gtk.PACK_DIRECTION_BTT


class MenuShell(gtk.Container):
    """Base class for MenuBar and Menu.

    It does children management and some low level event handlers.
    """

    # This should be a callable that returns a gtk.Menu ready to pop up
    context_menu_factory = None

    # default placement of submenus attached to the menu item children
    submenu_placement = gtk.TOP_BOTTOM

    def __init__(self, gadget):
        """Constructor

        gadget must be a Gazpacho Gadget representing the menubar it's
        being edited.
        """
        gtk.Container.__init__(self)

        self.gadget = gadget # Gazpacho associated gadget

        self.children = []
        self.active_menu_item = None
        self.parent_menu_shell = None

        self.active = False
        self.have_grab = False
        self.have_xgrab = False
        self.ignore_leave = False
        self.ignore_enter = False

        self.button = 0
        self.activate_time = 0

        self.take_focus = True

    def append(self, child):
        """Add child at the end of the children list"""
        self.insert(child, len(self.children))

    def prepend(self, child):
        """Add child at the begining of the children list"""
        self.insert(child, 0)

    def insert(self, child, position):
        """Add the children to the list at the specific position"""
        self.children.insert(position, child)
        child.set_parent(self)

    def to_xml(self, document):
        """Returns a XML node with the representation of this menushell"""
        tag = self.__class__.__name__.lower()
        element = document.createElement(tag)
        for child_node in self._get_children_nodes(document):
            element.appendChild(child_node)
        return element

    def _get_children_nodes(self, document):
        """Helper method to the to_xml method

        Returns a list of xml nodes corresponding to our children
        """
        ret = []
        for child in self.children:
            if child.submenu:
                node = child.submenu.to_xml(document)
            else:
                node = child.to_xml(document)

            if node:
                ret.append(node)
        return ret

    def load(self, xml_node):
        """Inverse to_xml method: creates a menushell from a xml node"""
        uim = self.gadget.project.uim
        default_action_group = uim.get_action_group('DefaultActions')
        for node in xml_node.childNodes:
            if node.nodeType != node.ELEMENT_NODE:
                continue

            name = node.getAttribute('action')
            action = default_action_group.get_action(name)
            if action:
                menuitem = MenuItem(action.label,
                                    self.gadget, default_action_group)
                menuitem.set_action(action)
            else:
                menuitem = SeparatorMenuItem()

            parent_is_menubar = isinstance(self, MenuBar)

            if node.hasChildNodes() or parent_is_menubar:
                submenu = Menu(self.gadget)
                submenu.load(node)
                menuitem.set_submenu(submenu)

            menuitem.show_all()

            self.insert(menuitem, len(self.children) - 1)

    # GtkWidget methods
    def do_realize(self):
        """Overrides widget_class->realize"""
        self.set_flags(self.flags() | gtk.REALIZED)

        mask = (gtk.gdk.EXPOSURE_MASK | gtk.gdk.BUTTON_PRESS_MASK |
                gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.KEY_PRESS_MASK |
                gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK)

        self.window = gtk.gdk.Window(
            self.get_parent_window(),
            x=self.allocation.x,
            y=self.allocation.y,
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gtk.gdk.WINDOW_CHILD,
            wclass=gtk.gdk.INPUT_OUTPUT,
            event_mask=self.get_events() | mask)

        self.window.set_user_data(self)
        self.style.attach(self.window)

        self.style.set_background(self.window, gtk.STATE_NORMAL)

    def do_button_press_event(self, event):
        """Overrides widget_class->button_press_event

        The reason for overriding this method is to popup the context menu
        with options to edit the selected item.
        """
        if event.button == 3:
            if self.context_menu_factory:
                menu_item = gtkutils.get_event_widget(event)
                if (menu_item and isinstance(menu_item, MenuItem) and
                    not isinstance(menu_item, (AddMenuItem, AddActionItem))):
                    popup = self.context_menu_factory(menu_item)
                    popup.popup(None, None, None, event.button, event.time)
                    return True

        elif self.parent_menu_shell:
            return self.parent_menu_shell.event(event)

        elif not self.active or self.button != 0:
            self._activate()
            self.button = event.button
            menu_item = self.get_item(event)
            if menu_item and menu_item.is_selectable():
                if (menu_item.parent == self and
                    menu_item != self.active_menu_item):
                    self.activate_time = event.time
                    self.select_item(menu_item)
        else:
            widget = gtkutils.get_event_widget(event)
            if widget == self:
                self.deactivate()

        return True

    def do_button_release_event(self, event):
        """Overrides widget_class->button_release_event"""
        if self.active:
            if self.button != 0 and event.button != self.button:
                self.button = 0
                if self.parent_menu_shell:
                    return self.parent_menu_shell.event(event)
            self.button = 0
            menu_item = self.get_item(event)
            deactivate = True

            if event.time - self.activate_time > MENU_SHELL_TIMEOUT:
                if (menu_item and self.active_menu_item == menu_item and
                    menu_item.is_selectable()):
                    if menu_item.submenu is None:
                        self.activate_menu_item(menu_item)
                        return True
                    else:
                        menu_item.select()
                        return True
                elif menu_item and not menu_item.is_selectable():
                    deactivate = False
                elif self.parent_menu_shell:
                    self.active = True
                    self.parent_menu_shell.event(event)
                    return True

                if menu_item and self.active_menu_item == menu_item:
                    deactivate = False
            else: # a very fast press-release
                self.activate_time = 0
                deactivate = False

            if deactivate:
                self.deactivate()

        return True

    def do_enter_notify_event(self, event):
        """Overrides widget_class->enter_notify_event"""
        if self.active:
            menu_item = gtkutils.get_event_widget(event)
            if (not menu_item or (isinstance(menu_item, MenuItem) and
                                  not menu_item.is_selectable())):
                return True

            if (menu_item.parent == self and
                self.active_menu_item != menu_item and
                isinstance(menu_item, MenuItem)):
                if self.ignore_enter:
                    return True

                if (event.detail != gtk.gdk.NOTIFY_INFERIOR and
                    menu_item.state != gtk.STATE_PRELIGHT and
                    not isinstance(menu_item, AddMenuItem)):
                    self.select_item(menu_item)

            elif self.parent_menu_shell:
                self.parent_menu_shell.event(event)
        return True

    def do_leave_notify_event(self, event):
        """Overrides widget_class->leave_notify_event"""
        if gtkutils.widget_visible(self):
            event_widget = gtkutils.get_event_widget(event)

            if (not event_widget or
                not isinstance(event_widget, MenuItem)):
                return True

            menu_item = event_widget

            if not menu_item.is_selectable():
                return True

            if (self.active_menu_item == menu_item and
                menu_item.submenu is None):
                if (event.detail != gtk.gdk.NOTIFY_INFERIOR and
                    menu_item.state != gtk.STATE_NORMAL):
                    self.deselect()

            elif self.parent_menu_shell:
                self.parent_menu_shell.event(event)

        return True

    # GtkContainer methods
    def do_add(self, widget):
        """Overrides container_class->add"""
        self.append(widget)

    def do_remove(self, widget):
        """Overrides container_class->remove"""
        was_visible = gtkutils.widget_visible(widget)
        self.children.remove(widget)

        if widget == self.active_menu_item:
            self.active_menu_item.deselect()
            self.active_menu_item = None

        widget.unparent()

        if was_visible:
            self.queue_resize()

    def do_forall(self, internal, callback, data):
        """Overrides container_class->forall"""
        for child in self.children:
            callback(child, data)

    def _activate(self):
        """Do a GTK+ grab and change the internal state to active"""
        if not self.active:
            self.grab_add()
            self.have_grab = True
            self.active = True

    def deactivate(self):
        """Change the state to not active and deselect the active item
        if there is one. Also ungrab at the GTK+ and GDK level.
        """
        if self.active:
            self.button = 0
            self.active = False
            self.activate_time = 0

            if self.active_menu_item:
                self.active_menu_item.deselect()
                self.active_menu_item = None

            if self.have_grab:
                self.have_grab = False
                self.grab_remove()

            if self.have_xgrab:
                display = self.get_display()
                self.have_xgrab = False
                display.pointer_ungrab()
                display.keyboard_ungrab()

    def is_item(self, child):
        """Helper method to get_item. True if child is a direct or indirect
        child of self. It can be a child of a submenu (indirect).
        """
        parent = child.parent
        while parent and isinstance(parent, MenuShell):
            if parent == self:
                return True
            parent = parent.parent_menu_shell

        return False

    def get_item(self, event):
        """Return the menu item over which the event occured"""
        menu_item = gtkutils.get_event_widget(event)

        while (menu_item and not isinstance(menu_item, MenuItem)):
            menu_item = menu_item.parent

        if (menu_item and self.is_item(menu_item)):
            return menu_item

    def can_select_item(self, menu_item):
        """True if menu_item can be selected"""
        if (not self.active) or (not self.active_menu_item == menu_item):
            return True
        return False

    def select_item(self, menu_item):
        """Selects menu_item if that is possible.

        This will probably mean that a submenu is popup.
        """
        if self.can_select_item(menu_item):
            self.deselect()

            if not menu_item.is_selectable():
                return

            self.active_menu_item = menu_item

            pack_dir = self.get_pack_direction()
            if (pack_dir == PACK_DIRECTION_TTB or
                pack_dir == PACK_DIRECTION_BTT):
                self.active_menu_item.set_placement(gtk.LEFT_RIGHT)
            else:
                placement = self.__class__.submenu_placement
                self.active_menu_item.set_placement(placement)

            self.active_menu_item.select()

    def deselect(self):
        """Unselect the active menu item if there is one.

        This will probably means that a submenu is popdown.
        """
        if self.active_menu_item:
            self.active_menu_item.deselect()
            self.active_menu_item = None

    def get_pack_direction(self):
        """Returns the pack direction"""
        return PACK_DIRECTION_LTR

    def activate_menu_item(self, menu_item):
        """Activate the menu_item. This will mean start editing its label"""
        # first we end editing all the children
        for child in self.children:
            if child.editing:
                child.end_editing()
        menu_item.activate()

gobject.type_register(MenuShell)

#
# MenuBar widget
#

BORDER_SPACING = 0
DEFAULT_IPADDING = 1

class MenuBar(MenuShell):
    """Editable MenuBar

    You can add menus to this bar by clicking on the special
    'Click to create menu' item.

    You can edit existing menus by right clicking on them and using the
    context menu.

    You can edit submenus by poping up them like a standard Menu Bar
    """

    context_menu_factory = contextmenu.MenuBarContextMenu
    submenu_placement = gtk.TOP_BOTTOM

    def __init__(self, gadget):
        """Constructor. Initialize the bar and put an AddMenuItem item"""
        MenuShell.__init__(self, gadget)

        self.child_pack_direction = PACK_DIRECTION_LTR
        self.pack_direction = PACK_DIRECTION_LTR

        item = AddMenuItem(self.gadget)
        item.show()
        self.append(item)

    def to_xml(self, document):
        """See MenuShell.to_xml"""
        element = super(MenuBar, self).to_xml(document)
        element.setAttribute('name', self.gadget.name)
        element.setAttribute('action', self.gadget.name)
        return element

    def update_ui(self):
        """Updates the UI definition for the gadget this MenuBar is editing

        It uses a Gazpacho command to update the UI definition in the project
        UI Manager.
        """
        dom = xml.dom.getDOMImplementation()
        document = dom.createDocument(None, None, None)
        ui_string = self.to_xml(document).toxml()
        cmd = CommandUpdateUIDefinitions(self.gadget, ui_string,
                                         'initial-state', False)
        command_manager.execute(cmd, self.gadget.project)

    def do_size_request(self, requisition):
        """Overrides widget_class->size_request"""
        requisition.width = 0
        requisition.height = 0

        if gtkutils.widget_visible(self):

            nchildren = 0

            for child in self.children:
                if gtkutils.widget_visible(child):
                    child.show_submenu_indicator = False
                    c_width, c_height = child.size_request()
                    toggle_size = child.toggle_size_request()

                    if (self.child_pack_direction == PACK_DIRECTION_LTR or
                        self.child_pack_direction == PACK_DIRECTION_RTL):
                        c_width += toggle_size
                    else:
                        c_height += toggle_size

                    if (self.pack_direction == PACK_DIRECTION_LTR or
                        self.pack_direction == PACK_DIRECTION_RTL):
                        requisition.width += c_width
                        requisition.height = max(requisition.height, c_height)
                    else:
                        requisition.width = max(requisition.width, c_width)
                        requisition.height += c_height

                    nchildren += 1

            ipadding = self.style_get_property('internal-padding')

            margin = self.border_width + ipadding + BORDER_SPACING * 2
            requisition.width += margin
            requisition.height += margin

            if self.get_shadow_type() != gtk.SHADOW_NONE:
                requisition.width += self.style.xthickness * 2
                requisition.height += self.style.ythickness * 2


    def do_size_allocate(self, allocation):
        """Overrides widget_class->size_allocate"""
        child_allocation = gtk.gdk.Rectangle()
        direction = self.get_direction()
        self.allocation = allocation

        if gtkutils.widget_realized(self):
            self.window.move_resize(allocation.x, allocation.y,
                                    allocation.width, allocation.height)

        ipadding = self.style_get_property('internal-padding')

        if self.children:
            child_allocation.x = self.border_width + ipadding + BORDER_SPACING
            child_allocation.y = self.border_width + ipadding + BORDER_SPACING

            if self.get_shadow_type() != gtk.SHADOW_NONE:
                child_allocation.x += self.style.xthickness
                child_allocation.y += self.style.ythickness

            if (self.pack_direction == PACK_DIRECTION_LTR or
                self.pack_direction == PACK_DIRECTION_RTL):
                child_allocation.height = max(1, allocation.height -
                                              child_allocation.y * 2)
                ltr_x = child_allocation.x

                for child in self.children:
                    toggle_size = child.toggle_size_request()
                    cr_width, cr_height = child.get_child_requisition()

                    if (self.child_pack_direction == PACK_DIRECTION_LTR or
                        self.child_pack_direction == PACK_DIRECTION_RTL):
                        cr_width += toggle_size
                    else:
                        cr_height += toggle_size

                    if gtkutils.widget_visible(child):
                        if ((direction == gtk.TEXT_DIR_LTR) ==
                            (self.pack_direction == PACK_DIRECTION_LTR)):
                            child_allocation.x = ltr_x
                        else:
                            child_allocation.x = (allocation.width
                                                  - cr_width - ltr_x)
                        child_allocation.width = cr_width
                        child.toggle_size_allocate(toggle_size)
                        child.size_allocate(child_allocation)

                        ltr_x += child_allocation.width
            else:
                child_allocation.width = max(1, allocation.width -
                                             child_allocation.x * 2)
                ltr_y = child_allocation.y

                for child in self.children:
                    toggle_size = child.toggle_size_request()
                    cr_width, cr_height = child.get_child_requisition()

                    if (self.child_pack_direction == PACK_DIRECTION_LTR or
                        self.child_pack_direction == PACK_DIRECTION_RTL):
                        cr_width += toggle_size
                    else:
                        cr_height += toggle_size

                    if gtkutils.widget_visible(child):
                        if ((direction == gtk.TEXT_DIR_LTR) ==
                            (self.pack_direction == PACK_DIRECTION_TTB)):
                            child_allocation.y = ltr_y
                        else:
                            child_allocation.y = (allocation.height
                                                  - cr_height - ltr_y)
                        child_allocation.height = cr_height
                        child.toggle_size_allocate(toggle_size)
                        child.size_allocate(child_allocation)

                        ltr_y += child_allocation.height

    def paint(self, area):
        """Helper method for the expose event handler"""
        if gtkutils.widget_drawable(self):
            border = self.border_width
            self.style.paint_box(self.window, self.state,
                                 self.get_shadow_type(), area, self, 'menubar',
                                 border, border,
                                 self.allocation.width - border * 2,
                                 self.allocation.height - border * 2)

    def do_expose_event(self, event):
        """Overrides widget_class->expose_event"""
        if gtkutils.widget_drawable(self):
            self.paint(event.area)

            MenuShell.do_expose_event(self, event)

        return False

    def get_shadow_type(self):
        """Returns the shadow used to draw the widget"""
        shadow_type = self.style_get_property('shadow-type')
        if not shadow_type:
            shadow_type = gtk.SHADOW_OUT
        return shadow_type

    def get_pack_direction(self):
        """Returns the pack direction"""
        return self.pack_direction

    def set_pack_direction(self, direction):
        """Set the pack direction and update the widget if necesary"""
        if self.pack_direction != direction:
            self.pack_direction = direction
            self.queue_resize()
            for child in self.children:
                child.queue_resize()

    def get_child_pack_direction(self):
        """Retrusn the pack direction for children"""
        return self.child_pack_direction

    def set_child_pack_direction(self, direction):
        """Set the children pack direction and update the widget if
        necessary"""
        if self.child_pack_direction != direction:
            self.child_pack_direction = direction
            self.queue_resize()
            for child in self.children:
                child.queue_resize()

gobject.type_register(MenuBar)
gtk.widget_class_install_style_property(MenuBar,
                                        ('shadow-type',
                                         gtk.ShadowType,
                                         'Shadow Type',
                                         'Style of bevel around the menubar',
                                         gtk.SHADOW_OUT,
                                         gobject.PARAM_READABLE))
desc = 'Amount of border space between the menubar shadow and the menu items'
gtk.widget_class_install_style_property(MenuBar,
                                        ('internal-padding',
                                         gobject.TYPE_INT,
                                         'Internal Padding',
                                         desc,
                                         0, 100, DEFAULT_IPADDING,
                                         gobject.PARAM_READABLE))

#
# Menu widget
#

DEFAULT_POPUP_DELAY = 225
DEFAULT_POPDOWN_DELAY = 1000

ATTACH_INFO_KEY = "gtk-menu-child-attach-info-key"
ATTACHED_MENUS = "gtk-attached-menus"

ATTACH_DATA_KEY = "gtk-menu-attach-data"

class Menu(MenuShell):
    """Editable Menu

    You can add actions to this menu by clicking on the special
    'Click to create action' item.

    You can edit existing menus by right clicking on them and using the
    context menu.

    You can edit submenus by poping up them like a standard Menu
    """

    context_menu_factory = contextmenu.MenuContextMenu
    submenu_placement = gtk.LEFT_RIGHT

    def __init__(self, gadget):
        """Constructor. Initialize the menu and put an AddActionItem item"""
        MenuShell.__init__(self, gadget)

        self.parent_menu_item = None
        self.old_active_menu_item = None
        self.position_func = None
        self.position_func_data = None
        self.toggle_size = 0

        self.toplevel = gobject.new(gtk.Window,
                                    type=gtk.WINDOW_POPUP,
                                    child=self)
        self.toplevel.connect('event', menu_window_event, self)
        self.toplevel.connect('size_request', menu_window_size_request, self)
        self.toplevel.set_resizable(False)
        self.toplevel.set_mnemonic_modifier(0)

        self.view_window = None
        self.bin_window = None

        self.seen_item_enter = False

        self.have_position = False
        self.x = 0
        self.y = 0

        # info used for the table
        self.heights = []

        self.monitor_num = 0

        self.have_layout = False
        self.n_rows = 0
        self.n_columns = 0

        item = AddActionItem(self.gadget)
        item.show_all()
        self.append(item)

    def to_xml(self, document):
        """See MenuShell.to_xml"""
        menuitem = self.get_attach_widget()
        if menuitem and menuitem.action:
            element = super(Menu, self).to_xml(document)
            element.setAttribute('name', menuitem.action.name)
            element.setAttribute('action', menuitem.action.name)
            return element

    def queue_resize(self):
        """Invalidates the current layout before calling the
        real queue_resize"""
        self.have_layout = False
        MenuShell.queue_resize(self)

    def ensure_layout(self):
        """Computes the table attachment for every child"""
        if not self.have_layout:

            # find extents of gridded portion
            max_right_attach = 1
            max_bottom_attach = 0

            for child in self.children:
                a_info = get_attach_info(child)

                if a_info.is_grid_attached():
                    max_bottom_attach = max(max_bottom_attach,
                                            a_info.bottom_attach)
                    max_right_attach = max(max_right_attach,
                                           a_info.right_attach)

            # find empty rows
            row_occupied = [False for i in range(max_bottom_attach)]
            for child in self.children:
                a_info = get_attach_info(child)

                if a_info.is_grid_attached():
                    for i in range(a_info.top_attach, a_info.bottom_attach):
                        row_occupied[i] = True

            # lay non-grid items out in those rows
            current_row = 0
            for child in self.children:
                a_info = get_attach_info(child)
                if not a_info.is_grid_attached():
                    while (current_row < max_bottom_attach and
                           row_occupied[current_row]):
                        current_row += 1

                    a_info.effective_left_attach = 0
                    a_info.effective_right_attach = max_right_attach
                    a_info.effective_top_attach = current_row
                    a_info.effective_bottom_attach = current_row + 1
                    current_row += 1

                else:
                    a_info.effective_left_attach = a_info.left_attach
                    a_info.effective_right_attach = a_info.right_attach
                    a_info.effective_top_attach = a_info.top_attach
                    a_info.effective_bottom_attach = a_info.bottom_attach
            self.n_rows = max(current_row, max_bottom_attach)
            self.n_columns = max_right_attach
            self.have_layout = True

    def get_n_columns(self):
        """Returns the number of columns (usually 1, 2 or 3)"""
        self.ensure_layout()
        return self.n_columns

    def get_n_rows(self):
        """Returns the number of rows"""
        self.ensure_layout()
        return self.n_rows

    def get_effective_child_attach(self, child):
        """Return the real table attachments for the child"""
        self.ensure_layout()

        a_info = get_attach_info(child)
        return (a_info.effective_left_attach, a_info.effective_right_attach,
                a_info.effective_top_attach, a_info.effective_bottom_attach)

    def do_destroy(self):
        """Overrides widget_class->destroy doing some extra cleanups"""
        data = self.get_data(ATTACH_DATA_KEY)
        if data:
            self.detach()

        if self.old_active_menu_item:
            del self.old_active_menu_item
            self.old_active_menu_item = None

        if self.toplevel:
            self.toplevel.destroy()

        if self.heights:
            self.heights = []

        MenuShell.do_destroy(self)

    def attach_to_widget(self, attach_widget, detacher_func):
        """Atach the menu to another widget"""
        data = self.get_data(ATTACH_DATA_KEY)
        if data:
            print(('WARNING: attach_to_widget(): menu already attached to %s' %
                   data.attach_widget))
            return

        data = _MenuAttachData()
        data.attach_widget = attach_widget

        data.detacher = detacher_func
        self.set_data(ATTACH_DATA_KEY, data)
        menu_list = attach_widget.get_data(ATTACHED_MENUS)
        if not menu_list:
            menu_list = []
        if not self in menu_list:
            menu_list.append(self)

        attach_widget.set_data(ATTACHED_MENUS, menu_list)

        if self.state != gtk.STATE_NORMAL:
            self.set_state(gtk.STATE_NORMAL)

    def get_attach_widget(self):
        """Return the widget attached to the menu"""
        data = self.get_data(ATTACH_DATA_KEY)
        if data:
            return data.attach_widget

    def detach(self):
        """Isolates the menu again"""
        data = self.get_data(ATTACH_DATA_KEY)
        if not data:
            print('WARNING: menu is not attached')
            return

        self.set_data(ATTACH_DATA_KEY, None)
        if data.detacher:
            data.detacher(data.attach_widget, self)

        menu_list = data.attach_widget.get_data(ATTACHED_MENUS)
        menu_list.remove(self)
        if menu_list:
            data.attach_widget.set_data(ATTACHED_MENUS, menu_list)
        else:
            data.attach_widget.set_data(ATTACHED_MENUS, None)

        if gtkutils.widget_realized(self):
            self.unrealize()

    def do_remove(self, child):
        """Overrides container_class->remove"""
        # clear out old_active_menu_item if it matches the item we are removing
        if self.old_active_menu_item == child:
            self.old_active_menu_item = None

        MenuShell.do_remove(self, child)
        child.set_data(ATTACH_INFO_KEY, None)

        self.queue_resize()

    def insert(self, child, position):
        """Add a menuitem using the bin_window as the parent window"""
        if gtkutils.widget_realized(self):
            child.set_parent_window(self.bin_window)

        MenuShell.insert(self, child, position)

        self.queue_resize()

    def popup(self, parent_menu_shell, parent_menu_item, func, data, button,
              activate_time):
        """Shows the menu and mapped it on screen on the appropiate place"""

        self.parent_menu_shell = parent_menu_shell
        self.seen_item_enter = False

        # find the last viewable ancestor, and make an X grab on it
        parent = self
        xgrab_shell = None
        while parent:
            viewable = True

            tmp = parent

            while tmp:
                if not gtkutils.widget_mapped(tmp):
                    viewable = False
                    break
                tmp = tmp.parent

            if viewable:
                xgrab_shell = parent

            parent = parent.parent_menu_shell

        grab_keyboard = self.take_focus
        self.toplevel.set_accept_focus(grab_keyboard)

        if xgrab_shell and xgrab_shell != self:
            if gtkutils.popup_grab_on_window(xgrab_shell.window,
                                             activate_time, grab_keyboard):
                self.have_xgrab = True
        else:
            xgrab_shell = self
            transfer_window = self.grab_transfer_window_get()
            if gtkutils.popup_grab_on_window(transfer_window,
                                             activate_time, grab_keyboard):
                self.have_xgrab = True

        if not self.have_xgrab:
            self.parent_menu_shell = None
            self.grab_transfer_window_destroy()
            return

        self.active = True
        self.button = button

        current_event = gtk.get_current_event()
        if current_event:
            if ((current_event.type != gtk.gdk.BUTTON_PRESS) and
                (current_event.type != gtk.gdk.ENTER_NOTIFY)):
                self.ignore_enter = True
        else:
            self.ignore_enter = True

        parent_toplevel = None
        if parent_menu_shell:
            parent_toplevel = parent_menu_shell.get_toplevel()
        else:
            attach_widget = self.get_attach_widget()
            if attach_widget:
                parent_toplevel = attach_widget.get_toplevel()

        if parent_toplevel and isinstance(parent_toplevel, gtk.Window):
            self.toplevel.set_transient_for(parent_toplevel)

        self.parent_menu_item = parent_menu_item
        self.position_func = func
        self.position_func_data = data
        self.activate_time = activate_time

        self.show()

        self.position()

        alloc = gtk.gdk.Rectangle()
        alloc.width, alloc.height = self.toplevel.size_request()
        self.toplevel.size_allocate(alloc)

        self.realize()

        self.toplevel.show()

        if xgrab_shell == self:
            gtkutils.popup_grab_on_window(self.window, activate_time,
                                          grab_keyboard)

        self.grab_add()

    def popdown(self):
        """Hides the menu releasing any grab previously adquired"""
        self.parent_menu_shell = None
        self.active = False
        self.ignore_enter = False

        self.have_position = False

        if self.active_menu_item:
            self.old_active_menu_item = self.active_menu_item

        self.deselect()

        self.toplevel.hide()
        self.toplevel.set_transient_for(None)

        self.window.get_display().pointer_ungrab(0)
        gtk.gdk.keyboard_ungrab(0)

        self.hide()

        self.have_xgrab = False
        self.grab_remove()

        self.grab_transfer_window_destroy()

    def get_active(self):
        """Returns the active menu item"""
        if not self.old_active_menu_item:

            for child in self.children:
                if child.child:
                    self.old_active_menu_item = child

        return self.old_active_menu_item

    def set_active(self, index):
        """Sets the active menu item"""
        if index < len(self.children):
            child = self.children[index]
            if child.child:
                self.old_active_menu_item = child

    def do_can_activate_accel(self, signal_id):
        """Override widget_class->can_activate_accel"""
        awidget = self.get_attach_widget()
        if awidget:
            return awidget.can_activate_accel(signal_id)
        else:
            return gtkutils.widget_is_sensitive(self)

    def reposition(self):
        """Position the menu again"""
        if gtkutils.widget_drawable(self):
            self.position()

    def get_toplevel(self):
        """Return the toplevel widget this menu is related to going up through
        the menu hierarchy recursively"""
        attach = self.get_attach_widget()
        if isinstance(attach, MenuItem):
            attach = attach.parent

        if isinstance(attach, Menu):
            return attach.get_toplevel()
        elif isinstance(attach, gtk.Widget):
            toplevel = attach.get_toplevel()
            if gtkutils.widget_toplevel(toplevel):
                return toplevel

    def reorder_child(self, child, position):
        """Change the child position"""
        if child in self.children:
            self.children.remove(child)
            self.children.insert(child, position)

            self.queue_resize()

    def do_style_set(self, previous_style):
        """Sets the style changing the background of the 3 gdk windows"""
        if gtkutils.widget_realized(self):
            self.style.set_background(self.bin_window, gtk.STATE_NORMAL)
            self.style.set_background(self.view_window, gtk.STATE_NORMAL)
            self.style.set_background(self.window, gtk.STATE_NORMAL)

    def do_realize(self):
        """Overrides widget_class->realize"""
        self.set_flags(self.flags() | gtk.REALIZED)
        mask = (gtk.gdk.EXPOSURE_MASK | gtk.gdk.KEY_PRESS_MASK |
                gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK)
        attrs = {
            'window_type': gtk.gdk.WINDOW_CHILD,
            'x': self.allocation.x,
            'y': self.allocation.y,
            'width': self.allocation.width,
            'height': self.allocation.height,
            'wclass': gtk.gdk.INPUT_OUTPUT,
            'event_mask': self.get_events() | mask,
            }
        self.window = gtk.gdk.Window(self.get_parent_window(), **attrs)
        self.window.set_user_data(self)

        border_width = self.border_width
        vertical_padding = self.style_get_property('vertical-padding')
        horizontal_padding = self.style_get_property('horizontal-padding')

        attrs['x'] = border_width + self.style.xthickness + horizontal_padding
        attrs['y'] = border_width + self.style.ythickness + vertical_padding
        attrs['width'] = max(1, self.allocation.width - attrs['x'] * 2)
        attrs['height'] = max(1, self.allocation.height - attrs['y'] * 2)

        self.view_window = gtk.gdk.Window(self.window, **attrs)
        self.view_window.set_user_data(self)

        attrs['x'] = 0
        attrs['y'] = 0
        attrs['width'] = max(1, self.allocation.width -
                             (border_width +
                              self.style.xthickness +
                              horizontal_padding) * 2)
        attrs['height'] = max(1, self.allocation.height -
                              (border_width +
                               self.style.ythickness +
                               vertical_padding) * 2)

        self.bin_window = gtk.gdk.Window(self.view_window, **attrs)
        self.bin_window.set_user_data(self)

        for child in self.children:
            child.set_parent_window(self.bin_window)

        self.set_style(self.style.attach(self.window))
        self.style.set_background(self.bin_window, gtk.STATE_NORMAL)
        self.style.set_background(self.view_window, gtk.STATE_NORMAL)
        self.style.set_background(self.window, gtk.STATE_NORMAL)

        self.bin_window.show()
        self.view_window.show()

    def grab_transfer_window_get(self):
        """Gets (creating if necessary) a window used to grab"""
        window = self.get_data('gtk-menu-transfer-window')
        if not window:
            window = gtk.gdk.Window(
                self.get_root_window(), x=-100, y=-100, width=10, height=10,
                window_type=gtk.gdk.WINDOW_TEMP, wclass=gtk.gdk.INPUT_ONLY,
                override_redirect=True, event_mask=0)
            window.set_user_data(self)
            window.show()
            self.set_data('gtk-menu-transfer-window', window)

        return window

    def grab_transfer_window_destroy(self):
        """Destroys the grab transfer window"""
        window = self.get_data('gtk-menu-transfer-window')
        if window:
            window.set_user_data(None)
            window.destroy()
            self.set_data('gtk-menu-transfer-window', None)

    def do_unrealize(self):
        """Overrides widget_class->unrealize"""
        self.grab_transfer_window_destroy()

        self.view_window.set_user_data(None)
        self.view_window.destroy()
        self.view_window = None

        self.bin_window.set_user_data(None)
        self.bin_window.destroy()
        self.bin_window = None

        MenuShell.do_unrealize(self)

    def do_size_request(self, requisition):
        """Overrides widget_class->size_request"""
        requisition.width = 0
        requisition.height = 0

        max_toggle_size = 0
        max_accel_width = 0

        n_rows = self.get_n_rows()
        self.heights = [0 for i in range(n_rows)]

        for child in self.children:
            if not gtkutils.widget_visible(child):
                continue

            left, right, top, bottom = self.get_effective_child_attach(child)
            child.show_submenu_indicator = True
            c_width, c_height = child.size_request()
            toggle_size = child.toggle_size_request()

            max_toggle_size = max(max_toggle_size, toggle_size)
            max_accel_width = max(max_accel_width, child.accelerator_width)

            part = c_width / (right - left)
            requisition.width = max(requisition.width, part)

            part = max(c_height, toggle_size) / (bottom - top)
            self.heights[top] = max(self.heights[top], part)

        for i in range(n_rows):
            requisition.height += self.heights[i]

        requisition.width += max_toggle_size + max_accel_width
        requisition.width *= self.get_n_columns()

        vertical_padding = self.style_get_property('vertical-padding')
        horizontal_padding = self.style_get_property('horizontal-padding')

        requisition.width += (self.border_width + horizontal_padding +
                              self.style.xthickness) * 2
        requisition.height += (self.border_width + vertical_padding +
                               self.style.ythickness) * 2

        self.toggle_size = max_toggle_size

    def do_size_allocate(self, allocation):
        """Overrides widget_class->size_allocate"""
        self.allocation = allocation
        cr_width, cr_height = self.get_child_requisition()

        vertical_padding = self.style_get_property('vertical-padding')
        horizontal_padding = self.style_get_property('horizontal-padding')

        x = self.border_width + self.style.xthickness + horizontal_padding
        y = self.border_width + self.style.ythickness + vertical_padding

        width = max(1, allocation.width - x * 2)
        height = max(1, allocation.height - y * 2)

        cr_width -= x * 2
        cr_height -= y * 2

        if gtkutils.widget_realized(self):
            self.window.move_resize(allocation.x, allocation.y,
                                    allocation.width, allocation.height)
            self.view_window.move_resize(x, y, width, height)


        if self.children:

            n_columns = self.get_n_columns()
            n_rows = self.get_n_rows()

            base_width = width / n_columns

            child_allocation = gtk.gdk.Rectangle()

            for child in self.children:
                if gtkutils.widget_visible(child):
                    (left, right,
                     top, bottom) = self.get_effective_child_attach(child)

                    if self.get_direction() == gtk.TEXT_DIR_RTL:
                        left, right = n_columns - right, n_columns - left

                    child_allocation.width = (right - left) * base_width
                    child_allocation.height = 0
                    child_allocation.x = left * base_width
                    child_allocation.y = 0

                    for i in range(bottom):
                        if i < top:
                            child_allocation.y += self.heights[i]
                        else:
                            child_allocation.height += self.heights[i]

                    child.toggle_size_allocate(self.toggle_size)
                    child.size_allocate(child_allocation)
                    child.queue_draw()

            # resize the item window
            if gtkutils.widget_realized(self):
                height = 0
                for i in range(n_rows):
                    height += self.heights[i]
                width = n_columns * base_width

                self.bin_window.resize(width, height)

    def paint(self, event):
        """Helper metod for the expose event handler"""
        vertical_padding = self.style_get_property('vertical-padding')
        horizontal_padding = self.style_get_property('horizontal-padding')

        border_x = (self.border_width + self.style.xthickness +
                    horizontal_padding)
        border_y = (self.border_width + self.style.ythickness +
                    vertical_padding)
        width, height = self.window.get_size()

        if event.window == self.window:
            self.style.paint_box(self.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                                 None, self, 'menu', 0, 0, -1, -1)

        elif event.window == self.bin_window:
            self.style.paint_box(self.bin_window, gtk.STATE_NORMAL,
                                 gtk.SHADOW_OUT, None, self, 'menu',
                                 - border_x, - border_y, width, height)

    def do_expose_event(self, event):
        """Overrides widget_class->expose_event"""
        if gtkutils.widget_drawable(self):
            self.paint(event)

            MenuShell.do_expose_event(self, event)

        return False

    def do_button_press_event(self, event):
        """Overrides widget_class->button_press_event"""
        # As we do some event propagation in MenuShell event handlers we
        # need to make sure this is the right event type
        if event.type != gtk.gdk.BUTTON_PRESS:
            return False

        return MenuShell.do_button_press_event(self, event)

    def do_button_release_event(self, event):
        """Overrides widget_class->button_release_event"""
        # As we do some event propagation in MenuShell event handlers we
        # need to make sure this is the right event type
        if event.type != gtk.gdk.BUTTON_RELEASE:
            return False

        return MenuShell.do_button_release_event(self, event)

    def do_motion_notify_event(self, event):
        """Overrides widget_class->motion_notify_event"""
        menu_item = gtkutils.get_event_widget(event)
        if (not menu_item or
            not isinstance(menu_item, MenuItem) or
            not isinstance(menu_item.parent, Menu)):
            return False

        menu_shell = menu_item.parent

        if definitely_within_item(menu_item, event.x, event.y):
            menu_shell.activate_time = 0

        need_enter = menu_shell.ignore_enter

        if not menu_item.is_selectable():
            menu_shell.deselect()
            return False

        if need_enter:
            menu_shell.ignore_enter = False

            width, height = event.window.get_size()

            if 0 <= event.x < width and 0 <= event.y < height:
                send_event = gtk.gdk.Event(gtk.gdk.ENTER_NOTIFY)

                send_event.window = event.window
                send_event.time = event.time
                send_event.send_event = True
                send_event.x_root = event.x_root
                send_event.y_root = event.y_root
                send_event.x = event.x
                send_event.y = event.y

                return self.event(send_event)

        return False

    def do_enter_notify_event(self, event):
        """Overrides widget_class->enter_notify_event"""
        menu_item = gtkutils.get_event_widget(event)
        if menu_item and isinstance(menu_item, MenuItem):
            menu = menu_item.parent

            if menu and isinstance(menu, Menu):
                if menu.seen_item_enter:
                    menu.activate_time = 0
                elif (event.detail != gtk.gdk.NOTIFY_NONLINEAR and
                      event.detail != gtk.gdk.NOTIFY_NONLINEAR_VIRTUAL):
                    if definitely_within_item(menu_item, event.x, event.y):
                        menu.activate_time = 0

                menu.seen_item_enter = True

        return MenuShell.do_enter_notify_event(self, event)

    def do_leave_notify_event(self, event):
        """Overrides widget_class->leave_notify_event"""
        menu_item = gtkutils.get_event_widget(event)

        if not menu_item or  not isinstance(menu_item, MenuItem):
            return True

        if (self.active_menu_item is not None and
            menu_item.submenu is not None and
            menu_item.submenu_placement == gtk.LEFT_RIGHT):
            if menu_item.submenu.active:
                return True
            elif menu_item == self.active_menu_item:
                self.deselect()
                return True

        return MenuShell.do_leave_notify_event(self, event)

    def deactivate(self):
        """Deactivates the menu hiding it and its parents"""
        parent = self.parent_menu_shell

        self.activate_time = 0
        self.popdown()

        if parent:
            parent.deactivate()

    def position(self):
        """Moves our toplevel window to the right position on screen"""
        screen = self.get_screen()

        pointer_screen, x, y, mask = screen.get_display().get_pointer()

        req_width, req_height = self.size_request()

        if pointer_screen != screen:
            x = max(0, (screen.get_width() - req_width) / 2)
            y = max(0, (screen.get_height() - req_height) / 2)

        self.monitor_num = screen.get_monitor_at_point(x, y)

        if not gtkutils.widget_visible(self.toplevel):
            self.toplevel.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_MENU)

        if self.position_func:
            x, y, push_in = self.position_func(self, False,
                                               self.position_func_data)

            if self.monitor_num < 0:
                self.monitor_num = screen.get_monitor_at_point(x, y)

            monitor = screen.get_monitor_geometry(self.monitor_num)
        else:
            xthickness = self.style.xthickness
            ythickness = self.style.ythickness
            rtl = self.get_direction() == gtk.TEXT_DIR_RTL

            monitor = screen.get_monitor_geometry(self.monitor_num)

            space_left = x - monitor.x
            space_right = monitor.x + monitor.width - x - 1
            space_above = y - monitor.y
            space_below = monitor.y + monitor.height - y - 1

            needed_width = req_width - xthickness

            if needed_width <= space_left or needed_width <= space_right:
                if (rtl and needed_width <= space_left or
                    not rtl and needed_width > space_right):
                    x = x + xthickness - req_width + 1
                else:
                    x = x - xthickness

            elif req_width <= monitor.width:
                if space_left > space_right:
                    x = monitor.x
                else:
                    x = monitor.x + monitor.width - req_width
            else:
                if rtl:
                    x = monitor.x + monitor.width - req_width
                else:
                    x = monitor.x

            needed_height = req_height - ythickness

            if needed_height <= space_above or needed_height <= space_below:
                if needed_height <= space_below:
                    y = y - ythickness
                else:
                    y = y + ythickness - req_height + 1

                y = gtkutils.clamp(y, monitor.y,
                                   monitor.y + monitor.height - req_height)

            elif needed_height > space_below and needed_height > space_above:
                if space_below >= space_above:
                    y = monitor.y + monitor.height - req_height
                else:
                    y = monitor.y

            else:
                y = monitor.y

        x = gtkutils.clamp(x, monitor.x,
                           max(monitor.x,
                               monitor.x + monitor.width - req_width))

        if self.active:
            self.have_position = True
            self.x = x
            self.y = y

        if y + req_height > monitor.y + monitor.height:
            req_height = (monitor.y + monitor.height) - y

        if y < monitor.y:
            req_height -= monitor.y - y
            y = monitor.y

        self.toplevel.move(x, y)

    def reparent(self, new_parent, unrealize):
        """Change our parent"""
        if unrealize:
            self.parent.remove(self)
            new_parent.add(self)
        else:
            MenuShell.reparent(self, new_parent)

    def show_all(self):
        """Shows all widgets except ourselves"""
        self.foreach(gtk.Widget.show_all)

    def hide_all(self):
        """Hides all widgets except ourselves"""
        self.foreach(gtk.Widget.hide_all)

    def attach(self, child,
               left_attach, right_attach, top_attach, bottom_attach):
        """Attaches the child with the given table attach information"""
        if child.parent is None or child.parent == self:
            return
        if left_attach < right_attach:
            return
        if top_attach < bottom_attach:
            return

        a_info = get_attach_info(child)
        a_info.left_attach = left_attach
        a_info.right_attach = right_attach
        a_info.top_attach = top_attach
        a_info.bottom_attach = top_attach

        if not child.parent:
            self.append(child) # this call child.set_parent(self)

        self.queue_resize()

gobject.type_register(Menu)
desc = 'Extra space at the top and bottom of the menu'
gtk.widget_class_install_style_property(Menu,
                                        ('vertical-padding',
                                         gobject.TYPE_INT,
                                         'Vertical Padding',
                                         desc,
                                         0, 100, 1,
                                         gobject.PARAM_READABLE))
desc = 'Extra space at the left and right of the menu'
gtk.widget_class_install_style_property(Menu,
                                        ('horizontal-padding',
                                         gobject.TYPE_INT,
                                         'Horizontal Padding',
                                         desc,
                                         0, 100, 0,
                                         gobject.PARAM_READABLE))
desc = 'When the menu is a submenu, position it this number of pixels offset vertically'
gtk.widget_class_install_style_property(Menu,
                                        ('vertical-offset',
                                         gobject.TYPE_INT,
                                         'Vertical Offset',
                                         desc,
                                         -100, 100, 0,
                                         gobject.PARAM_READABLE))
desc = 'When the menu is a submenu, position it this number of pixels offset horizontally'
gtk.widget_class_install_style_property(Menu,
                                        ('horizontal-offset',
                                         gobject.TYPE_INT,
                                         'Horizontal Offset',
                                         desc,
                                         -100, 100, -2,
                                         gobject.PARAM_READABLE))

# Utility clases and functions for the Menu widget
class _MenuAttachData(object):
    """Internal class used as a data container for menu attachments"""
    attach_widget = None
    detacher = None

class AttachInfo(object):
    """Class holding the information about a widget position inside a menu"""
    def __init__(self):
        """Dummy constructor"""
        self.left_attach = -1
        self.right_attach = -1
        self.top_attach = -1
        self.bottom_attach = -1
        self.effective_left_attach = 0
        self.effective_right_attach = 0
        self.effective_top_attach = 0
        self.effective_bottom_attach = 0

    def is_grid_attached(self):
        """True is the attachment is set after initialization"""
        return (self.left_attach >= 0 and self.right_attach >= 0 and
                self.top_attach >= 0 and self.bottom_attach >= 0)

def get_attach_info(child):
    """Returns the attachment information for a child"""
    a_info = child.get_data(ATTACH_INFO_KEY)
    if not a_info:
        a_info = AttachInfo()
        child.set_data(ATTACH_INFO_KEY, a_info)
    return a_info

def menu_window_event(window, event, menu):
    """Event handler for the GtkWindow of a Menu"""
    handled = False

    if event.type == gtk.gdk.KEY_PRESS or event.type == gtk.gdk.KEY_RELEASE:
        handled = menu.event(event)

    return handled

def menu_window_size_request(window, requisition, menu):
    """Size request handler for the GtkWindow of a Menu"""
    if menu.have_position:
        screen = window.get_screen()
        monitor = screen.get_monitor_geometry(menu.monitor_num)

        if menu.y + requisition.height > monitor.y + monitor.height:
            requisition.height = monitor.y + monitor.height - menu.y

        if menu.y < monitor.y:
            requisition.height -= monitor.y - menu.y

def check_threshold(start_x, start_y, x, y):
    """Helper function for definetely_within_item"""
    return abs(start_x - x) > 8 or abs(start_y - y) > 8

def definitely_within_item(menu_item, x, y):
    """True if the menu_item is point (x, y) is inside the menu_item"""
    width, height = menu_item.event_window.get_size()
    return (check_threshold(0, 0, x, y) and
            check_threshold(width - 1, 0, x, y) and
            check_threshold(width - 1, height - 1, x, y) and
            check_threshold(0, height - 1, x, y))

#
# MenuItem widget
#

class MenuItem(gtk.Item):
    """Editable MenuItem

    You can click on the menuitem label and an entry will replace it allowing
    you to edit the label
    """
    __gsignals__ = {
        'activate': (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_ACTION,
                     gobject.TYPE_NONE, tuple()),
        }

    def __init__(self, text, gadget=None, action_group=None):
        """Constructor"""
        gtk.Item.__init__(self)

        self.set_flags(self.flags() | gtk.NO_WINDOW)

        self.event_window = None
        self.submenu = None
        self.toggle_size = 0
        self.show_submenu_indicator = False
        if self.get_direction() == gtk.TEXT_DIR_RTL:
            self.submenu_direction = gtk.DIRECTION_LEFT
        else:
            self.submenu_direction = gtk.DIRECTION_RIGHT
        self.submenu_placement = gtk.TOP_BOTTOM

        self.accelerator_width = 0 # the Menu class uses this

        self.image = None

        self.label = gtk.Label(text)
        self.label.set_property('xalign', 0.0)

        # This entry is used in edit mode
        self.entry = gtk.Entry()
        self.entry.set_has_frame(False)
        self.entry.connect('activate', self._on_entry__activate)
        self.entry.connect('key-press-event', self._on_entry__key_press_event)

        # By default we are not in edit mode
        self.editing = False
        self.add(self.label)

        # Gazpacho stuff
        self.gadget = gadget
        self.action_group = action_group
        self.action = None

    def to_xml(self, document):
        """Returns a XML node with the representation of this menuitem"""
        if self.action:
            element = document.createElement('menuitem')
            element.setAttribute('name', self.action.name)
            element.setAttribute('action', self.action.name)
            return element

    def set_action(self, action):
        """Set the action updating the image and other internal widgets"""
        self.action = action
        self.label.set_text(action.label)
        if action.stock_id:
            image = gtk.image_new_from_stock(action.stock_id,
                                             gtk.ICON_SIZE_MENU)
            image.show()
            self.set_image(image)

    def do_destroy(self):
        """Overrides widget_class->destroy"""
        if self.submenu:
            self.submenu.destroy()

        gtk.Item.do_destroy(self)

    def set_submenu(self, submenu):
        """Set the submenu associated with this item"""
        if self.submenu != submenu:
            self.remove_submenu()
            self.submenu = submenu

            if submenu:
                submenu.attach_to_widget(self, detacher)

            if self.parent:
                self.queue_resize()

    def remove_submenu(self):
        """Removes the submenu"""
        if self.submenu:
            self.submenu.detach()

    def set_placement(self, placement):
        """Set the submenu placement"""
        self.submenu_placement = placement

    def set_image(self, image):
        """Sets the small icon to the left of the label in LTR"""
        if self.image != image:
            if self.image:
                self.image.unparent()
            self.image = image
            image.set_parent(self)
            self.queue_resize()

    def activate(self):
        """Emits the activate signal"""
        self.emit('activate')

    def do_activate(self):
        """Activate default handler, which start editing"""
        self.start_editing()

    def start_editing(self):
        """Replaces the label by the entry and grab the focus to let the
        user change the label"""
        self.editing = True

        self.entry.show()
        self.label.hide()

        self.entry.set_text(self.label.get_text())

        self.remove(self.label)
        self.add(self.entry)

        self.entry.grab_add()
        self.entry.grab_focus()

        self.queue_draw()

    def end_editing(self, cancel=False):
        """Finish editing by updating the label and replacing the entry with
        the label. If cancel is True, it just replace the entry by the label.

        It also updates (or creates) the gazpacho action associated
        """
        # First we update our internal state
        self.editing = False

        self.entry.grab_remove()

        self.label.show()
        self.entry.hide()

        if not cancel:
            self.label.set_text(self.entry.get_text())

        self.remove(self.entry)
        self.add(self.label)

        if isinstance(self.parent, MenuBar):
            self.parent.active = False
        self.queue_draw()

        if not self.gadget or cancel:
            return

        # Then, we update gazpacho state
        project = self.gadget.project

        label = self.label.get_text()
        name = self._label_to_name(label)

        if self.action:
            # update the associated action
            values = {
                'name' : name,
                'label': label,
                'short_label': self.action.short_label,
                'is_important': self.action.is_important,
                'stock_id': self.action.stock_id,
                'tooltip': self.action.tooltip,
                'accelerator': self.action.accelerator,
                'callback': self.action.callback,
                }
            cmd = CommandEditAction(self.action, values, project)
            command_manager.execute(cmd, project)
        else:
            # create the associated action
            new_gact = GAction(self.action_group,
                               name,  # name
                               label, # label
                               None,  # short label
                               False, # is important?
                               None,  # stock id
                               None,  # tooltip
                               None,  # accelerator
                               None)  # callback
            self.action = new_gact
            cmd = CommandAddRemoveAction(self.action_group, new_gact, True)
            command_manager.execute(cmd, project)

            # create the UI definition
            menu_bar = self.get_menu_bar()
            menu_bar.update_ui()

    def _label_to_name(self, label):
        """Creates a unique action name from its label"""
        name = label.replace(' ', '_')
        name = name.lower()
        basic_name = name
        count = 2
        while name in self.action_group.get_action_names():
            name = '%s-%d' % (basic_name, count)
            count += 1
        return name

    def _on_entry__activate(self, entry):
        """When the user clicks enter we finish editing"""
        self.end_editing()

    def _on_entry__key_press_event(self, entry, event):
        if event.keyval == gtk.keysyms.Escape:
            self.end_editing(cancel=True)
            if not self.action:
                self.parent.remove(self)
            return True

        return False

    def _get_minimum_width(self):
        """Minimum width based on 7 characters and the image"""
        context = self.get_pango_context()
        metrics = context.get_metrics(self.style.font_desc,
                                      context.get_language())
        height = metrics.get_ascent() + metrics.get_descent()

        ret = pango.PIXELS(7 * height)

        if self.image:
            width, height = self.image.size_request()
            ret = max(ret, height)

        return ret

    def _get_pack_directions(self):
        """Returns packs directions"""
        if isinstance(self.parent, MenuBar):
            pack_dir = self.parent.get_pack_direction()
            child_pack_dir = self.parent.get_child_pack_direction()
        else:
            pack_dir = PACK_DIRECTION_LTR
            child_pack_dir = PACK_DIRECTION_LTR
        return (pack_dir, child_pack_dir)

    def do_size_request(self, requisition):
        """Overrides widget_class->size_request"""
        horizontal_padding = self.style_get_property('horizontal-padding')

        pack_dir, child_pack_dir = self._get_pack_directions()

        requisition.width = self.border_width + self.style.xthickness * 2
        requisition.height = self.border_width + self.style.ythickness * 2

        if ((pack_dir == PACK_DIRECTION_LTR or
            pack_dir == PACK_DIRECTION_RTL) and
            (child_pack_dir == PACK_DIRECTION_LTR or
             child_pack_dir == PACK_DIRECTION_RTL)):
            requisition.width += 2 * horizontal_padding
        elif ((pack_dir == PACK_DIRECTION_TTB or
               pack_dir == PACK_DIRECTION_BTT) and
              (child_pack_dir == PACK_DIRECTION_TTB or
               child_pack_dir == PACK_DIRECTION_BTT)):
            requisition.height += 2 * horizontal_padding

        if self.child and gtkutils.widget_visible(self.child):
            child_width, child_height = self.child.size_request()
            requisition.width += child_width
            requisition.height += child_height

            if self.submenu and self.show_submenu_indicator:
                arrow_spacing = self.style_get_property('arrow-spacing')

                requisition.width += child_height
                requisition.width += arrow_spacing
                requisition.width = max(requisition.width,
                                        self._get_minimum_width())

        else: # separator item
            requisition.height += 4

    def do_size_allocate(self, allocation):
        """Overrides widget_class->size_allocate"""
        direction = self.get_direction()

        pack_dir, child_pack_dir = self._get_pack_directions()

        self.allocation = allocation

        if self.child:
            horizontal_padding = self.style_get_property('horizontal_padding')
            child_allocation = gtk.gdk.Rectangle()
            child_allocation.x = self.border_width + self.style.xthickness
            child_allocation.y = self.border_width + self.style.ythickness

            if ((pack_dir == PACK_DIRECTION_LTR or
                 pack_dir == PACK_DIRECTION_RTL) and
                (child_pack_dir == PACK_DIRECTION_LTR or
                 child_pack_dir == PACK_DIRECTION_RTL)):
                child_allocation.x += horizontal_padding
            elif ((pack_dir == PACK_DIRECTION_TTB or
                   pack_dir == PACK_DIRECTION_BTT) and
                  (child_pack_dir == PACK_DIRECTION_TTB or
                   child_pack_dir == PACK_DIRECTION_BTT)):
                child_allocation.y += horizontal_padding

            temp_width = allocation.width - child_allocation.x * 2
            child_allocation.width = max(1, temp_width)

            temp_height = allocation.height - child_allocation.y * 2
            child_allocation.height = max(1, temp_height)

            if (child_pack_dir == PACK_DIRECTION_LTR or
                child_pack_dir == PACK_DIRECTION_RTL):
                if ((direction == gtk.TEXT_DIR_LTR) ==
                    (child_pack_dir != PACK_DIRECTION_RTL)):
                    child_allocation.x += self.toggle_size
                child_allocation.width -= self.toggle_size
            else:
                if ((direction == gtk.TEXT_DIR_LTR) ==
                    (child_pack_dir != PACK_DIRECTION_BTT)):
                    child_allocation.y += self.toggle_size
                child_allocation.height -= self.toggle_size

            child_allocation.x += self.allocation.x
            child_allocation.y += self.allocation.y

            c_req_width, c_req_height = self.child.get_child_requisition()

            if self.submenu and self.show_submenu_indicator:
                if direction == gtk.TEXT_DIR_RTL:
                    child_allocation.x += c_req_width
                child_allocation.width -= c_req_height

            if child_allocation.width < 1:
                child_allocation.width = 1

            self.child.size_allocate(child_allocation)

            if self.image:
                width, height = self.image.get_child_requisition()
                image_allocation = gtk.gdk.Rectangle()
                image_allocation.x = self.border_width + self.style.xthickness
                image_allocation.y = self.border_width + self.style.ythickness
                y = (self.allocation.height - height) / 2
                image_allocation.y += max(y, 0) + self.allocation.y
                image_allocation.width = width
                image_allocation.height = height
                self.image.size_allocate(image_allocation)

        if gtkutils.widget_realized(self):
            self.event_window.move_resize(allocation.x, allocation.y,
                                          allocation.width, allocation.height)

        if self.submenu:
            self.submenu.reposition()

    def do_realize(self):
        """Overrides widget_class->realize to create event_window"""
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = self.get_parent_window()

        self.event_window = gtk.gdk.Window(
            self.window,
            window_type=gtk.gdk.WINDOW_CHILD,
            x=self.allocation.x,
            y=self.allocation.y,
            width=self.allocation.width,
            height=self.allocation.height,
            wclass=gtk.gdk.INPUT_ONLY,
            event_mask=(self.get_events() |
                        gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.ENTER_NOTIFY_MASK |
                        gtk.gdk.LEAVE_NOTIFY_MASK |
                        gtk.gdk.POINTER_MOTION_MASK))

        self.event_window.set_user_data(self)

        self.set_style(self.style.attach(self.window))

    def do_unrealize(self):
        """Overrides widget_class->unrealize to destroy event_window"""
        self.event_window.set_user_data(None)
        self.event_window.destroy()
        self.event_window = None
        gtk.Item.do_unrealize(self)

    def do_map(self):
        """Overrides widget_class->map to map the event_window"""
        gtk.Item.do_map(self)
        self.event_window.show()

    def do_unmap(self):
        """Overrides widget_class->unmap to unmap the event_window"""
        self.event_window.hide()
        gtk.Item.do_unmap(self)

    def paint(self, area):
        """Helper method for the expose event handler"""
        if gtkutils.widget_drawable(self):
            x = self.allocation.x + self.border_width
            y = self.allocation.y + self.border_width
            width = self.allocation.width - self.border_width * 2
            height = self.allocation.height - self.border_width * 2

            if self.state == gtk.STATE_PRELIGHT and self.child:
                sel_shdw_type = self.style_get_property('selected-shadow-type')
                self.style.paint_box(self.window, gtk.STATE_PRELIGHT,
                                     sel_shdw_type, area, self, 'menuitem',
                                     x, y, width, height)

            if self.submenu and self.show_submenu_indicator:
                direction = self.get_direction()

                hor_padding = self.style_get_property('horizontal-padding')

                context = self.child.get_pango_context()
                metrics = context.get_metrics(self.child.style.font_desc,
                                              context.get_language())
                ascent = metrics.get_ascent()
                descent = metrics.get_descent()

                arrow_size = (pango.PIXELS(ascent + descent) -
                              2 * self.style.ythickness)
                arrow_extent = int(arrow_size * 0.8)

                shadow_type = gtk.SHADOW_OUT
                if self.state == gtk.STATE_PRELIGHT:
                    shadow_type = gtk.SHADOW_IN

                if direction == gtk.TEXT_DIR_LTR:
                    arrow_x = x + width - hor_padding - arrow_extent
                    arrow_type = gtk.ARROW_RIGHT
                else:
                    arrow_x = x + hor_padding
                    arrow_type = gtk.ARROW_LEFT

                arrow_y = y + (height - arrow_extent) / 2

                self.style.paint_arrow(self.window, self.state, shadow_type,
                                       area, self, 'menuitem', arrow_type,
                                       True, arrow_x, arrow_y,
                                       arrow_extent, arrow_extent)
            elif not self.child:
                hor_padding = self.style_get_property('horizontal-padding')

                sx1 = (self.allocation.x + hor_padding +
                       self.style.xthickness)
                sx2 = (self.allocation.x + self.allocation.width -
                       hor_padding - self.style.xthickness - 1)
                sep_y = self.allocation.y + (self.allocation.height -
                                             self.style.ythickness) / 2
                self.style.paint_hline(self.window, gtk.STATE_NORMAL,
                                       area, self, 'menuitem',
                                       sx1, sx2, sep_y)

    def do_expose_event(self, event):
        """Overrides widget_class->expose"""
        if gtkutils.widget_drawable(self):
            self.paint(event.area)

            gtk.Item.do_expose_event(self, event)

        return False

    def do_select(self):
        """Select signal handler. Pop up the submenu"""
        if self.submenu and not gtkutils.widget_mapped(self.submenu):
            self._popup_submenu()

        self.set_state(gtk.STATE_PRELIGHT)
        self.queue_draw()

    def do_deselect(self):
        """Deselect signal handler. Pop down the submenu"""
        if self.submenu:
            self.submenu.popdown()

        self.set_state(gtk.STATE_NORMAL)
        self.queue_draw()

    def toggle_size_request(self):
        """Compute the size request for the toggle area"""
        if self.image:
            width, height = self.image.size_request()
            return width
        else:
            return 0

    def toggle_size_allocate(self, allocation):
        """Allocate the size for the toggle area"""
        self.toggle_size = allocation

    def _popup_submenu(self):
        """Shows the submenu"""
        if gtkutils.widget_is_sensitive(self.submenu):
            self.submenu.take_focus = self.parent.take_focus

            self.submenu.popup(self.parent, self, menu_item_position_menu,
                               self, self.parent.button, 0)

    def do_show_all(self):
        """Show the children including the submenu"""
        if self.submenu:
            self.submenu.show_all()

        if self.child:
            self.child.show_all()

        if self.image:
            self.image.show_all()

        self.show()

    def do_hide_all(self):
        """Hide the children including the submenu"""
        self.hide()

        if self.image:
            self.image.hide_all()

        if self.child:
            self.child.hide_all()

        if self.submenu:
            self.submenu.hide_all()

    def do_forall(self, include_internals, callback, data):
        """Iterates through the label and image"""
        if self.child:
            callback(self.child, data)

        if self.image:
            callback(self.image, data)

    def do_remove(self, child):
        """Remove the label or the image"""
        if self.image == child:
            was_visible = gtkutils.widget_visible(child)
            child.unparent()
            self.image = None
            if gtkutils.widget_visible(self) and was_visible:
                self.queue_resize()
        else:
            gtk.Item.do_remove(self, child)

    def is_selectable(self):
        """True if the item can be selected"""
        if (not self.child or
            isinstance(self, SeparatorMenuItem) or
            not gtkutils.widget_is_sensitive(self) or
            not gtkutils.widget_visible(self)):
            return False

        return True

    def is_first(self):
        """True if the item is the first child of its parent"""
        if self.parent:
            first = self.parent.children[0]
            if first == self:
                return True
        return False

    def is_last(self):
        """True if the item is the last child of its parent"""
        if self.parent:
            last = self.parent.children[-2] # last element is the placeholder
            if last == self:
                return True
        return False

    def is_new_group(self):
        """True is there is a Separator just before this item"""
        if self.parent:
            i = self.parent.children.index(self)
            if i > 0:
                prev = self.parent.children[i - 1]
                if isinstance(prev, SeparatorMenuItem):
                    return True
        return False

    def get_menu_bar(self):
        """Return the top menubar this menuitem belongs to"""
        parent = self.parent
        if isinstance(parent, MenuBar):
            return parent
        elif isinstance(parent, Menu):
            menuitem = parent.get_attach_widget()
            return menuitem.get_menu_bar()

gobject.type_register(MenuItem)
gtk.widget_class_install_style_property(MenuItem,
                                        ('selected-shadow-type',
                                         gtk.ShadowType,
                                         'Selected Shadow Type',
                                         'Shadow type when item is selected',
                                         gtk.SHADOW_NONE,
                                         gobject.PARAM_READABLE))

gtk.widget_class_install_style_property(MenuItem,
                                        ('horizontal-padding',
                                         gobject.TYPE_INT,
                                         'horizontal-padding',
                                         'Padding to left and right',
                                         0, 100, 3,
                                         gobject.PARAM_READABLE))
gtk.widget_class_install_style_property(MenuItem,
                                        ('arrow-spacing',
                                         gobject.TYPE_INT,
                                         'Arrow Spacing',
                                         'Space between label and arrow',
                                         0, 100, 10,
                                         gobject.PARAM_READABLE))

class SeparatorMenuItem(MenuItem):
    """Item for separator entries"""
    def __init__(self):
        """Basic constructor"""
        gtk.Item.__init__(self) # note we don't call MenuItem __init__

        self.set_flags(self.flags() | gtk.NO_WINDOW)

        self.submenu = None
        self.toggle_size = 0
        self.show_submenu_indicator = False
        if self.get_direction() == gtk.TEXT_DIR_RTL:
            self.submenu_direction = gtk.DIRECTION_LEFT
        else:
            self.submenu_direction = gtk.DIRECTION_RIGHT
        self.submenu_placement = gtk.TOP_BOTTOM

        self.accelerator_width = 0 # the Menu class uses this

        self.image = None

        self.label = None
        self.entry = None
        self.editing = False
        self.action = None

    def to_xml(self, document):
        """Returns a xml node representing this item"""
        element = document.createElement('separator')
        return element

gobject.type_register(SeparatorMenuItem)

def get_offsets(menu):
    """Helper function for menu_item_position_menu"""
    horizontal_offset = menu.style_get_property('horizontal-offset')
    vertical_offset = menu.style_get_property('vertical-offset')
    horizontal_padding = menu.style_get_property('horizontal-padding')
    vertical_padding = menu.style_get_property('vertical_padding')

    vertical_offset -= menu.style.ythickness
    vertical_offset -= vertical_padding
    horizontal_offset += horizontal_padding

    return (horizontal_offset, vertical_offset)

def menu_item_position_menu(menu_widget, push_in, menu_item):
    """Computes the position where the menu should be positioned given the
    menu_item"""
    if push_in:
        push_in = False

    direction = menu_item.get_direction()
    twidth, theight = menu_widget.size_request()

    screen = menu_widget.get_screen()

    monitor_num = screen.get_monitor_at_window(menu_item.event_window)
    if monitor_num < 0:
        monitor_num = 0

    monitor = screen.get_monitor_geometry(monitor_num)

    tx, ty = menu_item.window.get_origin()

    tx += menu_item.allocation.x
    ty += menu_item.allocation.y

    horizontal_offset, vertical_offset = get_offsets(menu_widget)

    if menu_item.submenu_placement == gtk.TOP_BOTTOM:
        if direction == gtk.TEXT_DIR_LTR:
            menu_item.submenu_direction = gtk.DIRECTION_RIGHT
        else:
            menu_item.submenu_direction = gtk.DIRECTION_LEFT
            tx += menu_item.allocation.width - twidth

        if ((ty + menu_item.allocation.height + theight) <=
            monitor.y + monitor.height):
            ty += menu_item.allocation.height
        elif ((ty - theight) >= monitor.y):
            ty -= theight
        elif (monitor.y + monitor.height -
              (ty + menu_item.allocation.height) > ty):
            ty += menu_item.allocation.height
        else:
            ty -= theight

    elif menu_item.submenu_placement == gtk.LEFT_RIGHT:
        if isinstance(menu_item.parent, Menu):
            parent_menu_item = menu_item.parent.parent_menu_item
        else:
            parent_menu_item = None

        parent_xthickness = menu_item.parent.style.xthickness

        if parent_menu_item:
            menu_item.submenu_direction = parent_menu_item.submenu_direction
        else:
            if direction == gtk.TEXT_DIR_LTR:
                menu_item.submenu_direction = gtk.DIRECTION_RIGHT
            else:
                menu_item.submenu_direction = gtk.DIRECTION_LEFT

        new_direction = None
        if menu_item.submenu_direction == gtk.DIRECTION_LEFT:
            if ((tx - twidth - parent_xthickness - horizontal_offset) >=
                monitor.x):
                tx -= twidth + parent_xthickness + horizontal_offset
            else:
                new_direction = gtk.DIRECTION_RIGHT
                tx += (menu_item.allocation.width + parent_xthickness +
                       horizontal_offset)

        elif menu_item.submenu_direction == gtk.DIRECTION_RIGHT:
            if ((tx + menu_item.allocation.width + parent_xthickness +
                 horizontal_offset +twidth) <= monitor.x + monitor.width):
                tx += (menu_item.allocation.width + parent_xthickness +
                       horizontal_offset)
            else:
                new_direction = gtk.DIRECTION_LEFT
                tx -= twidth + parent_xthickness + horizontal_offset


        if new_direction:
            menu_item.submenu_direction = new_direction

        ty += vertical_offset

        ty = gtkutils.clamp(ty, monitor.y,
                            max(monitor.y,
                                monitor.y + monitor.height - theight))

    x = gtkutils.clamp(tx, monitor.x,
                       max(monitor.x, monitor.x + monitor.width - twidth))
    y = ty

    return (x, y, push_in)

def detacher(menuitem, menu):
    """Function to detach menuitem from menu"""
    if not menuitem.submenu == menu:
        return

    menuitem.submenu = None


class AddMenuItem(MenuItem):
    """MenuItem that can add menus to a MenuBar"""
    def __init__(self, gadget):
        """Creates the menuitem with a 'Click to create menu' label"""
        text = _('Click to create menu')
        label = '<i><span foreground="darkgrey">%s</span></i>' % text
        MenuItem.__init__(self, label)

        self.gadget = gadget

        self.label.set_use_markup(True)

    def do_activate(self):
        """Creates a menuitem and a submenu for it"""
        project = self.gadget.project
        uim = project.uim
        default_action_group = uim.get_action_group('DefaultActions')
        if default_action_group:
            item = MenuItem(_('New Menu'), self.gadget, default_action_group)
            submenu = Menu(self.gadget)
            item.set_submenu(submenu)
            item.show_all()
            self.parent.insert(item, len(self.parent.children) - 1)
            item.activate()
        else:
            error(_('There is no action group to add this action to'))

    def do_select(self):
        """As soon as the item is selected it is activated"""
        self.activate()

    def to_xml(self, document):
        """An AddMenuItem is not serialized so this method returns None"""
        return None

class AddActionItem(MenuItem):
    """MenuItem that can add actions to a Menu"""
    def __init__(self, gadget):
        """Creates the menuitem with a 'Click to create action' label"""
        text = _('Click to create action')
        label = '<i><span foreground="darkgrey">%s</span></i>' % text
        MenuItem.__init__(self, label)

        self.gadget = gadget

        self.label.set_use_markup(True)

    def do_activate(self):
        """Creates a menuitem"""
        project = self.gadget.project
        uim = project.uim
        default_action_group = uim.get_action_group('DefaultActions')
        if default_action_group:
            item = MenuItem(_('New Action'), self.gadget, default_action_group)
            item.show_all()
            self.parent.insert(item, len(self.parent.children) - 1)
            item.activate()
        else:
            error(_('There is no action group to add this action to'))

    def to_xml(self, document):
        """An AddMenuItem is not serialized so this method returns None"""
        return None
