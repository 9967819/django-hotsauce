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

import operator
import xml.dom.minidom

import gtk
import gobject
from kiwi.ui.dialogs import BaseDialog

from gazpacho.i18n import _
from gazpacho.propertyeditor import PropertyEditorDialog
from gazpacho.util import select_iter
from gazpacho.command import Command
from gazpacho.commandmanager import command_manager

# XXX: Remove
def xml_filter_nodes(nodes, node_type):
    return [node for node in nodes if node.nodeType == node_type]

class UIEditor(PropertyEditorDialog):
    def __init__(self):
        # we can have a menubar or a toolbar here
        self.is_menu = True

        PropertyEditorDialog.__init__(self)
        self.uim = None

    def set_gadget(self, gadget, proxy):
        super(UIEditor, self).set_gadget(gadget, proxy)

        self.uim = gadget.project.uim

        if isinstance(gadget.widget, gtk.MenuBar):
            self.set_title(_('Editing menubar %s') % gadget.name)
            self.is_menu = True
        elif isinstance(gadget.widget, gtk.Toolbar):
            self.set_title(_('Editing toolbar %s') % gadget.name)
            self.is_menu = False
        else:
            raise ValueError(_('UIEditor is only for toolbars and menubars'))

        self._load_ui()

    # internal methods
    def _create_widgets(self):
        "Build the dialog window interface widgets"
        #XXX: Could this method be called build_editor_dialog?
        hbox = gtk.HBox(spacing=6)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        hbox.pack_start(sw, True, True)

        self.model = gtk.TreeStore(object)
        self.treeview = gtk.TreeView(self.model)
        self.treeview.connect('button-press-event',
                              self._on_treeview__button_press_event)
        self.treeview.connect('key-press-event',
                              self._on_treeview__key_press_event)
        selection = self.treeview.get_selection()
        selection.connect('changed', self._on_selection_changed)
        self.treeview.set_size_request(300, 300)
        sw.add(self.treeview)
        self.treeview.set_headers_visible(False)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        self.treeview.append_column(column)
        column.pack_start(renderer)
        column.set_cell_data_func(renderer, self._cell_data_function)

        v_button_box = gtk.VButtonBox()
        v_button_box.set_layout(gtk.BUTTONBOX_START)
        self.up = gtk.Button(stock=gtk.STOCK_GO_UP)
        self.up.connect('clicked', self._on_up_clicked)
        v_button_box.pack_start(self.up)
        self.down = gtk.Button(stock=gtk.STOCK_GO_DOWN)
        self.down.connect('clicked', self._on_down_clicked)
        v_button_box.pack_start(self.down)
        self.left = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.left.connect('clicked', self._on_left_clicked)
        self.right = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.right.connect('clicked', self._on_right_clicked)
        if self.is_menu:
            v_button_box.pack_start(self.left)
            v_button_box.pack_start(self.right)

#        hbox.pack_start(v_button_box, False, False)

        self.vbox.pack_start(hbox, True, True)

        h_button_box = gtk.HButtonBox()
        h_button_box.set_spacing(6)
        h_button_box.set_layout(gtk.BUTTONBOX_START)
        self.add = gtk.Button(stock=gtk.STOCK_ADD)
        self.add.connect('clicked', self._on_add_clicked)
        h_button_box.pack_start(self.add)
        self.remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove.connect('clicked', self._on_remove_clicked)
        h_button_box.pack_start(self.remove)
        self.vbox.pack_start(h_button_box, False, False)

        label = gtk.Label()
        label.set_markup('<small>%s</small>' % \
                         _('Press Escape to unselected an item'))
        self.vbox.pack_start(label, False, False)

    def _on_treeview__button_press_event(self, treeview, event):
        result = treeview.get_path_at_pos(int(event.x), int(event.y))
        if not result:
            selection = treeview.get_selection()
            selection.unselect_all()

    def _on_treeview__key_press_event(self, treeview, event):
        if event.keyval == gtk.keysyms.Escape:
            selection = treeview.get_selection()
            selection.unselect_all()

    def _load_node(self, xml_node, parent_iter):
        new_iter = self.model.append(parent_iter, (xml_node,))
        for child_node in xml_filter_nodes(xml_node.childNodes,
                                           xml_node.ELEMENT_NODE):
            self._load_node(child_node, new_iter)

    def _load_ui(self):
        # XXX right now we only allow to edit the initial state
        ui = self.uim.get_ui(self.gadget, 'initial-state')

        self.model.clear()
        if ui:
            xml_string = ui[0]
            self.xml_doc = xml.dom.minidom.parseString(xml_string)
            self.xml_doc.normalize()
            self.root_node = self.xml_doc.documentElement
            typename = self.root_node.tagName
        else:
            # create empty XML document
            self.xml_doc = xml.dom.getDOMImplementation().createDocument(None,
                                                                         None,
                                                                         None)
            if self.is_menu:
                typename = 'menubar'
            else:
                typename = 'toolbar'
            self.root_node = self._create_xml_node(self.xml_doc, typename,
                                                   self.gadget.name)
        for xml_node in xml_filter_nodes(self.root_node.childNodes,
                                         self.root_node.ELEMENT_NODE):
            self._load_node(xml_node, None)

        self._set_buttons_sensitiviness(typename)

    def _cell_data_function(self, column, cell, model, current_iter):
        xml_node = model[current_iter][0]
        typename = xml_node.tagName
        name = xml_node.getAttribute('name')
        if typename == 'separator':
            name = '<separator>'
        cell.set_property('text', name)

    def _get_selected_iter(self):
        selection = self.treeview.get_selection()
        return selection.get_selected()[1]

    def _create_xml_node(self, parent, typename, name):
        element = self.xml_doc.createElement(typename)
        element.setAttribute('name', name)
        if typename != 'separator':
            element.setAttribute('action', name)
        return parent.appendChild(element)

    def _set_buttons_sensitiviness(self, typename):
        "Set edit buttons sensitiveness depending on class"

        buttons = (self.add, self.remove, self.up, self.down, self.left,
                   self.right)
        sensitivity = {
            'menubar': (True, False, False, False, False, False),
            'menu': (True, True, True, True, False, True),
            'menuitem': (False, True, True, True, True, False),
            'toolbar':(True, False, False, False, False, False),
            'toolitem': (False, True, True, True, False, False ),
            'separator': (False, True, True, True, False, False),
            }
        for i, s in enumerate(sensitivity[typename]):
            buttons[i].set_sensitive(s)

    def _set_ui(self):
        ui_string = self.root_node.toxml()
        cmd = CommandUpdateUIDefinitions(self.gadget, ui_string,
                                         'initial-state')
        command_manager.execute(cmd, self.gadget.project)

    # callbacks
    def _on_selection_changed(self, selection):
        "Get selected element and set edit buttons sensitiveness for it"

        model, selected_iter = selection.get_selected()
        if selected_iter is not None:
            xml_node = model[selected_iter][0]
            name = xml_node.tagName
        else:
            name = self.root_node.tagName

        self._set_buttons_sensitiviness(name)

    def _on_add_clicked(self, button):
        selected_iter = self._get_selected_iter()
        # we are adding a toplevel
        selected_node = self.root_node
        if self.is_menu:
            if selected_iter:
                dialog_class = AddMenuitemDialog
                typename = 'menuitem'
                selected_node = self.model[selected_iter][0]
            else:
                typename = 'menu'
                dialog_class = AddMenuDialog
        else:
            dialog_class = AddToolitemDialog
            typename = 'toolitem'
            if selected_iter:
                selected_node = self.root_node
                selected_iter = None

        dialog = dialog_class(self.uim.get_action_groups(), self)
        response = dialog.run()
        if response != gtk.RESPONSE_OK:
            dialog.destroy()
            return

        if dialog.use_separator():
            typename = 'separator'
            name = 'sep'
        else:
            name = dialog.get_name()
        node = self._create_xml_node(selected_node, typename, name)
        new_iter = self.model.append(selected_iter, (node,))
        select_iter(self.treeview, new_iter)
        self._set_ui()

        dialog.destroy()

    def _on_remove_clicked(self, button):
        selected_iter = self._get_selected_iter()
        if selected_iter is None:
            return

        xml_node = self.model[selected_iter][0]
        self.model.remove(selected_iter)

        parent_node = xml_node.parentNode
        parent_node.removeChild(xml_node)

        self._set_ui()

    def _on_up_clicked(self, button):
        selected_iter = self._get_selected_iter()
        if selected_iter is None:
            return

        xml_node = self.model[selected_iter][0]
        parent_node = xml_node.parentNode
        previous_sibling = xml_node.previousSibling
        if previous_sibling is not None:
            print(previous_sibling)
            tmp_node = parent_node.removeChild(xml_node)
            parent_node.insertBefore(tmp_node, previous_sibling)
            # not update the TreeView
            selected_path = self.model.get_path(selected_iter)
            print(selected_path, type(selected_path))
            sibling_iter = self.model[selected_path[0] - 1].iter
            self.model.move_before(selected_iter, sibling_iter)

            self._set_ui()

    def _on_down_clicked(self, button):
        print('not implemented yet')

    def _on_left_clicked(self, button):
        print('not implemented yet')

    def _on_right_clicked(self, button):
        print('not implemented yet')


class ChooseActionDialog(BaseDialog):
    """Dialog to choose an action from a list"""
    def __init__(self, action_groups=[], toplevel=None):
        BaseDialog.__init__(self, parent=toplevel,
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.set_resizable(False)

        self.label = gtk.Label(_('Choose an action')+':')
        self.vbox.pack_start(self.label, False)

        # create a combo with all the actions
        model = gtk.ListStore(str)
        self.actions = gtk.ComboBox(model)
        renderer = gtk.CellRendererText()
        self.actions.pack_start(renderer)
        self.actions.add_attribute(renderer, 'text', 0)

        for action_group in action_groups:
            actions = action_group.get_actions()
            actions.sort(key=operator.attrgetter('name'))
            for action in actions:
                model.append(('%s/%s' % (action_group.name, action.name),))

        self.actions.set_active(0)

        self.vbox.pack_start(self.actions)

        self.set_default_response(gtk.RESPONSE_OK)

    def get_selected_action_name(self):
        model = self.actions.get_model()
        active_iter = self.actions.get_active_iter()
        if active_iter is not None:
            name = model[active_iter][0]
            action_name = name.split('/')[1]
            return action_name

    def use_separator(self):
        """Subclasses will probably override this"""
        return False

gobject.type_register(ChooseActionDialog)

class AddMenuDialog(ChooseActionDialog):
    def __init__(self, action_groups=[], toplevel=None):
        ChooseActionDialog.__init__(self, action_groups, toplevel)

        self.set_title(_('Adding a menu'))
        self.vbox.show_all()

    def get_name(self):
        return self.get_selected_action_name()

gobject.type_register(AddMenuDialog)

class AddToolitemDialog(AddMenuDialog):
    def __init__(self, action_groups=[], toplevel=None):
        AddMenuDialog.__init__(self, action_groups, toplevel)

        # put the combo in other place
        self.vbox.remove(self.actions)
        self.vbox.remove(self.label)

        hbox = gtk.HBox(spacing=6)
        self.select_action = gtk.RadioButton(None, _('Action'))
        self.select_separator = gtk.RadioButton(self.select_action,
                                                _('Separator'))

        hbox.pack_start(self.select_action, False, False)
        hbox.pack_start(self.actions)

        self.vbox.pack_start(hbox, False, False)
        self.vbox.pack_start(self.select_separator, False, False)

        self.set_title(_('Adding a toolitem'))
        self.vbox.show_all()

        if len(self.actions.get_model()) > 0:
            self.select_action.set_sensitive(True)
            self.select_action.set_active(True)
        else:
            self.select_action.set_sensitive(False)
            self.select_action.set_active(False)
            self.select_separator.set_active(True)

    def use_separator(self):
        return self.select_separator.get_active()

gobject.type_register(AddToolitemDialog)

class AddMenuitemDialog(AddToolitemDialog):
    def __init__(self, action_groups=[], toplevel=None):
        AddToolitemDialog.__init__(self, action_groups, toplevel)

        self.set_title(_('Adding a menuitem'))
        self.vbox.show_all()

gobject.type_register(AddMenuitemDialog)


class CommandUpdateUIDefinitions(Command):
    """
    Update the UI definitions for a UIManager based widget.
    """

    def __init__(self, gadget, ui_defs, ui_name, refresh=True):
        Command.__init__(self, _("Edit UI definitions"))
        self._gadget = gadget
        self._defs = ui_defs
        self._ui_name = ui_name
        # If this is set to False the UIM won't refresh the gtk widget and
        # you are responsible of doing so at some point
        self._refresh = refresh

    def execute(self):
        uim = self._gadget.project.uim
        old_defs = uim.get_ui(self._gadget, self._ui_name)[0]
        uim.update_ui(self._gadget, self._defs, self._ui_name, self._refresh)
        self._defs = old_defs

    def unifies(self, other):
        if isinstance(other, CommandUpdateUIDefinitions):
            return (self._gadget is other._gadget
                    and self._ui_name == other._ui_name)
        return False
