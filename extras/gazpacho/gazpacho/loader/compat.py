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

import xml.dom.minidom

import gtk
import gobject

from gazpacho import util
from gazpacho.i18n import _
from gazpacho.loader import tags

class Converter:
    def __init__(self, xml_node, uimanager, ui_definitions, signals):
        self.root_node = xml_node
        self.uimanager = uimanager
        self.ui_definitions = ui_definitions
        self.signals = signals
        self.widget_id = xml_node.getAttribute(tags.XML_TAG_ID)

    def build_widget(self):
        """This should be implemented by subclasses"""

class UIManagerBasedWidgetsConverter(Converter):
    """Superclass for converters of widgets based on UIManager like
    Toolbars and MenuBars
    """
    root_node_name = '' # subclasses should override this attribute

    def __init__(self, xml_node, uimanager, ui_definitions, signals):
        Converter.__init__(self, xml_node, uimanager, ui_definitions, signals)
        self.action_group = gtk.ActionGroup('Deprecated Actions for %s' % \
                                            self.widget_id)
        self.uimanager.insert_action_group(self.action_group, 0)

    def build_widget(self):
        new_doc = xml.dom.getDOMImplementation().createDocument(None, None,
                                                                None)
        root_node = new_doc.createElement('ui')
        new_doc.appendChild(root_node)

        widget_node = new_doc.createElement(self.root_node_name)
        root_node.appendChild(widget_node)

        widget_node.setAttribute('action', self.widget_id)
        widget_node.setAttribute('name', self.widget_id)

        for child_node in util.xml_child_widgets(self.root_node):
            self.build_child_widget(child_node, widget_node, new_doc)

        xml_string = new_doc.documentElement.toxml()
        merge_id = self.uimanager.add_ui_from_string(xml_string)
        obj = self.uimanager.get_widget('ui/%s' % self.widget_id)
        obj.set_data('merge_id', merge_id)

        if 'initial-state' in self.ui_definitions:
            other_xml_string = self.ui_definitions['initial-state']
            other_xml = xml.dom.minidom.parseString(other_xml_string)
            for node in [n for n in other_xml.childNodes if n.typeNode == n.ELEMENT_NODE]:
                new_doc.appendChild(node.cloneNode())
            xml_string = new_doc.documentElement.toxml()

        self.ui_definitions['initial-state'] = xml_string
        return obj

    def build_child_widget(self, xml_node, parent_node, new_doc):
        """This should be implemented by subclasses"""

    def create_action_from_node(self, xml_node, action_name):
        props = {'label' : action_name, 'tooltip': '', 'stock-id': None}
        for child_node in util.xml_filter_nodes(xml_node.childNodes,
                                                xml_node.ELEMENT_NODE):
            if child_node.tagName == tags.XML_TAG_PROPERTY:
                name, value = util.xml_parse_raw_property(child_node)
                if name == 'label':
                    props[name] = value
            elif child_node.tagName == tags.XML_TAG_SIGNAL:
                signal_name = child_node.getAttribute(tags.XML_TAG_NAME)
                if signal_name in ('clicked', 'activated'):
                    callback = child_node.getAttribute(tags.XML_TAG_HANDLER)
                    props['callback'] = callback

        action = gtk.Action(action_name, props['label'], props['tooltip'],
                            props['stock-id'])
        if 'callback' in list(props.keys()):
            if props['callback']:
                action.set_data(tags.SIGNAL_HANDLER, props['callback'])
                self.signals.append([action, 'activate', callback, None])
        self.action_group.add_action(action)

class ToolbarConverter(UIManagerBasedWidgetsConverter):
    root_node_name = 'toolbar'

    def build_child_widget(self, xml_node, parent_node, new_doc):
        if xml_node.tagName != tags.XML_TAG_WIDGET:
            return

        item_id = xml_node.getAttribute(tags.XML_TAG_ID)
        class_name = xml_node.getAttribute(tags.XML_TAG_CLASS)
        if class_name == 'GtkSeparatorToolItem':
            tool_node = new_doc.createElement('separator')
        else:
            tool_node = new_doc.createElement('toolitem')
            tool_node.setAttribute('action', item_id)
            tool_node.setAttribute('name', item_id)
            self.create_action_from_node(xml_node, item_id)

        parent_node.appendChild(tool_node)

class MenuBarConverter(UIManagerBasedWidgetsConverter):

    root_node_name = 'menubar'

    def build_child_widget(self, xml_node, parent_node, new_doc):
        if xml_node.tagName != tags.XML_TAG_WIDGET:
            return
        item_id = xml_node.getAttribute(tags.XML_TAG_ID)
        menu_node = new_doc.createElement('menu')
        menu_node.setAttribute('action', item_id)
        menu_node.setAttribute('name', item_id)
        parent_node.appendChild(menu_node)

        self.create_action_from_node(xml_node, item_id)

        for child_node in util.xml_child_widgets(xml_node):
            # this is the GtkMenu node. we skip top level GtkMenu nodes
            for subchild_node in util.xml_child_widgets(child_node):
                self.build_menu_item(subchild_node, menu_node, new_doc)

    def build_menu_item(self, xml_node, parent_node, new_doc):
        if xml_node.tagName != tags.XML_TAG_WIDGET:
            return
        item_id = xml_node.getAttribute(tags.XML_TAG_ID)
        # if the menuitem has children it is actually a menu
        children = util.xml_child_widgets(xml_node)
        if children:
            menu_node = new_doc.createElement('menu')
            menu_node.setAttribute('action', item_id)
            menu_node.setAttribute('name', item_id)
            self.create_action_from_node(xml_node, item_id)
            for child_node in util.xml_child_widgets(xml_node):
                self.build_menu_item(child_node, menu_node, new_doc)

        else:
            class_name = xml_node.getAttribute(tags.XML_TAG_CLASS)
            if class_name == 'GtkSeparatorMenuItem':
                menu_node = new_doc.createElement('separator')
            else:
                menu_node = new_doc.createElement('menuitem')
                menu_node.setAttribute('action', item_id)
                menu_node.setAttribute('name', item_id)
                self.create_action_from_node(xml_node, item_id)

        parent_node.appendChild(menu_node)

builders = {
    'GtkMenuBar': MenuBarConverter,
    'GtkToolbar': ToolbarConverter,
    }

def build_deprecated_widget(xml_node, uimanager, ui_definitions, signals):
    global builders
    klass = xml_node.getAttribute(tags.XML_TAG_CLASS)
    obj = builders[klass](xml_node, uimanager, ui_definitions, signals)
    return obj.build_widget()


class DeprecatedWidgetsDialog(gtk.Dialog):
    def __init__(self, window, widgets):
        gtk.Dialog.__init__(self,
                            title=_('Deprecated widgets found'),
                            parent=window,
                            flags=gtk.DIALOG_MODAL | \
                            gtk.DIALOG_DESTROY_WITH_PARENT | \
                            gtk.DIALOG_NO_SEPARATOR,
                            buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.set_border_width(12)
        self.vbox.set_spacing(6)

        msg = _('Gazpacho found the following deprecated widgets:')
        label = gtk.Label('<b><big>%s</big></b>' % msg)
        label.set_use_markup(True)
        self.vbox.pack_start(label, False)

        msg = '\n'.join(["- %s: %s" % (w.name, c) for w, c in widgets])
        label = gtk.Label(msg)
        self.vbox.pack_start(label, False)

        msg = _("They were converted to the equivalent newest widgets "
                "but please note that if\nyou save the file in Gazpacho "
                "it will not be compatible with Glade-2 anymore")
        label = gtk.Label('<small>%s</small>' % msg)
        label.set_use_markup(True)
        self.vbox.pack_start(label, False)

        self.vbox.show_all()

gobject.type_register(DeprecatedWidgetsDialog)
