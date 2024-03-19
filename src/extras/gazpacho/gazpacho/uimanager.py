# -*- test-case-name: gazpacho.unittest.test_uim.py -*-
# Copyright (C) 2004,2005 by SICEm S.L.
#               2005,2006 Async Open Source
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

from gazpacho.gaction import GAction, GActionGroup

default_actions = [
    # name, label, short_label, is_important,
    # tooltip, stock_id, callback, accelerator
    ('FileMenu', '_File', None, False,
     '', None, '', ''),
    ('New', '_New', None, False,
     'Create a new file', gtk.STOCK_NEW, '', '<control>N'),
    ('Open', '_Open', None, False,
     'Open a file', gtk.STOCK_OPEN, '', '<control>O'),
    ('Save', '_Save', None, True,
      'Save a file', gtk.STOCK_SAVE, '', '<control>S'),
    ('SaveAs', 'Save _As', None, False,
     'Save with a different name', gtk.STOCK_SAVE_AS, '', ''),
    ('Quit', '_Quit', None, False,
     'Quit the program', gtk.STOCK_QUIT, '', '<control>Q'),
    ('EditMenu', '_Edit', None, False,
     '', None, '', ''),
    ('Copy', '_Copy', None, False,
      'Copy selected object into the clipboard', gtk.STOCK_COPY, '',
      '<control>C'),
    ('Cut', 'Cu_t', None, False,
      'Cut selected object into the clipboard', gtk.STOCK_CUT, '',
      '<control>X'),
    ('Paste', '_Paste', None, False,
     'Paste object from the Clipboard', gtk.STOCK_PASTE, '', '<control>V'),
    ]

# XXX: Remove
def xml_filter_nodes(nodes, node_type):
    return [node for node in nodes if node.nodeType == node_type]

def strip_text_nodes(node):
    for child in node.childNodes[:]:
        strip_text_nodes(child)

    if node.nodeType == node.TEXT_NODE:
        node.parentNode.removeChild(node)

class GazpachoUIM(object):
    """Wrapper for the UIManager.

    Provides additional functionality to the standard UIManager
    """

    def __init__(self, project):

        self._project = project

        self.reset()

    def get_name(self):
        return self._uim_name

    def reset(self):
        self._uim = gtk.UIManager()
        self._uim_name = 'uimanager'

        # this dictionary maps gadgets with their ui definitions. Example:
        # { gadget1: {'initial-state' : (XML1, merge-id1)},
        #   gadget2: {'initial-state' : (XML2, merge-id2),
        #              'special-mode' : (XML3, merge-id3)},
        # }
        self._uis = {}

        self._action_groups = []

        # this dictionary is only used in the loading phase
        self._loaded_uis = {}

    def add_ui(self, gadget, xml_string, ui_name='initial-state'):
        "Add a ui definition for gadget with the name ui_name"
        if gadget not in self._uis:
            self._uis[gadget] = {}

        # add it to the uimanager
        merge_id = self._uim.add_ui_from_string(xml_string)
        self._uis[gadget][ui_name] = (xml_string, merge_id)

    def get_ui(self, gadget, ui_name=None):
        "Return a ui definition for gadget or all of them if ui_name is None"
        uis = self._uis.get(gadget)
        if ui_name and uis:
            return uis[ui_name]
        return uis

    def update_ui(self, gadget, xml, ui_name='initial-state',
                  refresh_widget=True):
        """Update the ui definition of gadget with name ui_name

        If the argument refresh_widget is True the gtk widget associated
        with gadget is created again with the new ui and the gadget is
        updated with this new widget
        """

        project = gadget.project
        if refresh_widget:
            # save the parent and the packing props before changing the uim
            old_widget = gadget.widget
            parent = old_widget.get_parent()
            if parent:
                props = {}
                ptype = type(parent)
                for pspec in gtk.container_class_list_child_properties(ptype):
                    props[pspec.name] = parent.child_get_property(old_widget,
                                                                  pspec.name)

                parent.remove(old_widget)

                # Update project. We have to check if the widget is still in
                # the project to play nice with widget name changes
                if project.get_gadget_by_name(old_widget.get_name()):
                    project.remove_widget(old_widget)

        # update the ui manager
        old_merge_id = self._uis[gadget][ui_name][1]
        self._uim.remove_ui(old_merge_id)
        self._uim.ensure_update()
        new_merge_id = self._uim.add_ui_from_string(xml)
        self._uis[gadget][ui_name] = (xml, new_merge_id)

        if refresh_widget:
            # update the gtk widget of gadget
            new_widget = self.get_widget(gadget)

            # copy the packing properties to the new widget
            if parent:
                parent.add(new_widget)

                for name, value in list(props.items()):
                    parent.child_set_property(new_widget, name, value)

            # finish widget configuration
            gadget.setup_widget(new_widget)

            # Update project
            project.add_widget(new_widget)

    def get_widget(self, gadget):
        self._uim.ensure_update()
        return self._uim.get_widget('/%s' % gadget.name)

    def add_action_group(self, action_group):
        if self._uim is None:
            self._uim = gtk.UIManager()

        self._action_groups.append(action_group)
        id1 = action_group.connect('add-action', self._project._add_action_cb)
        id2 = action_group.connect('remove-action',
                                   self._project._remove_action_cb)
        action_group.set_data('add_action_id', id1)
        action_group.set_data('remove_action_id', id2)

        action_group.create_gtk_action_group(self._uim)

    def remove_action_group(self, action_group):
        self._action_groups.remove(action_group)
        id1 = action_group.get_data('add_action_id')
        id2 = action_group.get_data('remove_action_id')
        action_group.disconnect(id1)
        action_group.disconnect(id2)

        action_group.destroy_gtk_action_group()

    def get_action_group(self, action_group_name):
        """Return an action group given its name or None if no action group
        with that name was found"""
        for gag in self._action_groups:
            if gag.get_name() == action_group_name:
                return gag

    def create_default_actions(self):
        """Create a set of default action groups inside a DefaultActions
        action group in the project this uim belongs to.
        Don't add them if they are already there.
        """
        # create the 'DefaultActions' action group
        gaction_group = None
        for gag in self._action_groups:
            if gag.name == 'DefaultActions':
                gaction_group = gag
                break
        # if not found, create it
        else:
            gag = GActionGroup('DefaultActions')
            self._project.add_action_group(gag)
            gaction_group = self._action_groups[-1]

        gaction_group.add_actions(default_actions)

    def update_widget_name(self, gadget):
        """Update the ui definitions of gadget with the new widget name"""
        if self._uim is None:
            raise RuntimeError("No UIManager has been created yet. Can not "
                               "update the name of the widget %s" % \
                               gadget.name)

        for ui_name, value in list(self._uis[gadget].items()):
            new_xml = self._change_ui_definition(value[0], gadget.name)
            self.update_ui(gadget, new_xml, ui_name)

    def _change_ui_definition(self, xml_string, new_name):
        "Change a ui definition of a widget to use a new_name for the widget"
        doc = minidom.parseString(xml_string)
        doc.documentElement.setAttribute('action', new_name)
        doc.documentElement.setAttribute('name', new_name)
        return doc.documentElement.toxml()

    def load(self, loader):
        """Get the UIManager of the loader and copy its content into
        this uimanager.

        Load also its ui definition spliting them into the widgets. When
        this uim is loaded the widgets it defines (menubars, toolbars, ...)
        are not loaded yet so we can't add the ui definitions into the
        self.uis dictionary. We use a temporary one until we load the
        widgets."""

        objs = [obj for obj in loader.get_widgets()
                        if isinstance(obj, gtk.UIManager)]
        if not objs:
            return

        if len(objs) >= 2:
            print('Warning: multiple uimanagers is not supported yet')

        gaction_callbacks = {}
        uimanager = objs[0]
        self._uim_name = uimanager.get_data('gazpacho::object-id')

        for signal_info in loader.get_signals():
            widget, signal, handler = signal_info[:3]
            if signal == "activate" and isinstance(widget, gtk.Action):
                gaction_callbacks[widget] = handler

        # read the action groups
        for ag in uimanager.get_action_groups():
            # only add the action group if we don't have it
            gag = self.get_action_group(ag.get_name())
            if not gag:
                gag = GActionGroup.new(ag)
                self.add_action_group(gag)
            for action in ag.list_actions():
                ga = GAction.new(action, gag)
                # only add the action if the action group does not have it
                if not gag.get_action(ga.name):
                    ga.callback = gaction_callbacks.get(action, '')
                    gag.add_action(ga)

        # load the ui definitions
        for ui_name, xml_string, merge_id in loader.get_ui_definitions():
            # we need to split this ui definition into several widgets
            doc = minidom.parseString(xml_string)
            self._split_ui(doc, ui_name, merge_id)

    def _split_ui(self, document, ui_name, merge_id):
        """Split a XML tree into several ones, each one with only a widget
        definition"""
        root = document.documentElement
        for node in xml_filter_nodes(root.childNodes, root.ELEMENT_NODE):
            xml_string = node.toxml()
            name = node.getAttribute('name')
            if name not in self._loaded_uis:
                self._loaded_uis[name] = []

            self._loaded_uis[name].append((ui_name, xml_string, merge_id))

    def load_widget(self, gadget, old_name):
        """Load the gadget replacing its widget by the one the uimanager
        has.

        old_name is the name the widget had before creating the gadget from
        it and we are inside a paste operation it will be different to the
        name the gadget has now.

        Also moves the dictionary self.loaded_uis into the self.uis"""

        if old_name not in self._loaded_uis:
            return

        self._uis[gadget] = {}
        for ui_name, xml_string, merge_id in self._loaded_uis[old_name]:
            if gadget.name != old_name:
                # we need to change the xml_string to change the widget name
                xml_string = self._change_ui_definition(xml_string,
                                                        gadget.name)

            merge_id = self._uim.add_ui_from_string(xml_string)
            self._uis[gadget][ui_name] = (xml_string, merge_id)

        del self._loaded_uis[old_name]

    def is_loading(self):
        return len(list(self._loaded_uis.keys())) > 0

    def remove_gadget(self, gadget):
        "Remove all the uidefinitions of gadget on the uimanager"
        for value in list(self._uis[gadget].values()):
            self._uim.remove_ui(value[1])

        del self._uis[gadget]

    def add_gadget(self, gadget, definitions):
        """Add an existing widget with its definitions to the uim.

        Also, update the widget of gadget after this change
        """
        self._uis[gadget] = {}
        for ui_name, value in list(definitions.items()):
            xml_string = value[0]
            merge_id = self._uim.add_ui_from_string(xml_string)
            self._uis[gadget][ui_name] = (xml_string, merge_id)

        widget = self.get_widget(gadget)
        gadget.setup_widget(widget)

    def save_ui_definitions(self, document, gadgets, version):
        """Return a list of XML nodes with the ui definitions of the
        gadgets we need to save
        """
        uis = self._group_ui_definitions_by_name(gadgets)
        uis = self._get_required_uis(uis, gadgets)

        nodes = []
        for ui_name, xml_list in list(uis.items()):
            ui_node = document.createElement('ui')
            ui_node.setAttribute('id', ui_name)

            uidef_node = document.createElement('ui')
            text_node = minidom.Text()
            text_node.data = '\n'
            uidef_node.appendChild(text_node)
            for xml_string in xml_list:
                tmp = minidom.parseString(xml_string)
                uidef_node.appendChild(tmp.documentElement)
            text_node = minidom.Text()
            text_node.data = '\n'
            uidef_node.appendChild(text_node)

            if version == 'gtkbuilder':
                strip_text_nodes(uidef_node)
                nodes.append(uidef_node)
            else:
                child = document.createCDATASection(uidef_node.toxml())
                ui_node.appendChild(child)
                nodes.append(ui_node)

        return nodes

    def get_ui_widgets(self, widget):
        """Get a list of all the widgets inside the hierarchy that are widgets
        related to a UI Manager (e.g. Toolbars and Menubars).
        """
        result = []
        if isinstance(widget, (gtk.Toolbar, gtk.MenuBar)):
            result.append(widget)

        elif isinstance(widget, gtk.Container):
            for child in widget.get_children():
                result += self.get_ui_widgets(child)

        return result

    def _group_ui_definitions_by_name(self, gadgets):
        """Group the ui definitions of this UI Manager by name.

        Only group those that belong to any of gadgets
        In the UIManager they are usually stored by widget.
        """
        uis = {}
        keys = list(self._uis.keys())
        keys.sort(lambda a, b: cmp(a.name, b.name))
        for gadget in keys:
            if gadget not in gadgets:
                continue
            ui_def = self._uis[gadget]
            for ui_name, value in list(ui_def.items()):
                xml_string = value[0]
                uis.setdefault(ui_name, []).append(xml_string)
        return uis

    def _get_required_uis(self, ui_definitions, gadgets):
        """Return the ui definitions that the gadgets are using"""
        # In this dict we decide if we need to save this ui or not
        # Initialy we don't save any ui
        uis_to_save = dict([(k, False) for k in list(ui_definitions.keys())])

        # now, let's loop through the widgets we need to save to see
        # if we need to save their uis
        for gadget in gadgets:
            gadget_uis = self.get_ui(gadget)
            if not gadget_uis:
                continue

            uis_names = list(gadget_uis.keys())
            for ui_name in uis_names:
                if ui_name in list(uis_to_save.keys()):
                    uis_to_save[ui_name] = True

        # so let's save the ui definitions
        for ui_name, save in list(uis_to_save.items()):
            if not save:
                del ui_definitions[ui_name]

        return ui_definitions

    def get_action_groups(self):
        return self._action_groups
