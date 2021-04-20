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

import io
from gettext import dgettext
import xml.dom
from xml.sax.saxutils import escape
import gobject
import gtk

from gazpacho import util
from gazpacho.choice import enum_to_string, flags_to_string
from gazpacho.placeholder import Placeholder
from gazpacho.gadget import Gadget
from gazpacho.properties import prop_registry, ObjectType

def write_xml(file, xml_node, indent=0, indent_increase=4):
    if xml_node.nodeType == xml_node.TEXT_NODE:
        file.write(xml_node.data)
        return
    elif xml_node.nodeType == xml_node.CDATA_SECTION_NODE:
        file.write('<![CDATA[%s]]>' % xml_node.data)
        return

    file.write(' '*indent)

    file.write('<%s' % xml_node.tagName)
    if len(xml_node.attributes) > 0:
        attr_string = ' '.join(['%s="%s"' % (n, v)
                                    for n, v in list(xml_node.attributes.items())])
        file.write(' ' + attr_string)

    children = [a for a in xml_node.childNodes
                    if a.nodeType != a.ATTRIBUTE_NODE]
    if children:
        has_text_child = False
        for child in children:
            if child.nodeType in (child.TEXT_NODE,
                                  child.CDATA_SECTION_NODE):
                has_text_child = True
                break

        if has_text_child:
            file.write('>')
        else:
            file.write('>\n')
        for child in children:
            write_xml(file, child, indent+indent_increase, indent_increase)

        if not has_text_child:
            file.write(' '*indent)
        file.write('</%s>\n' % xml_node.tagName)
    else:
        file.write('/>\n')

class XMLWriter:
    """
    @ivar _doc:
    @ivar _project:
    @ivar _version:
    @ivar _skip_external_references: If True we clear all object
       references that are not part of the current serialization
    @ivar _all_widgets: all widgets in the current serialization
    """
    def __init__(self, document=None, project=None):
        if not document:
            dom = xml.dom.getDOMImplementation()
            document = dom.createDocument(None, None, None)
        self._doc = document
        self._project = project
        self._version = "libglade"

        self._skip_external_references = False
        self._all_widgets = []

    def write(self, path, widgets, sizegroups, models, uim, domain, version):
        self._version = version
        root = self._write_root(widgets, domain)
        self._write_sizegroups(root, sizegroups)
        for model in models:
            self._write_model(root, model)
        self._write_widgets(root, widgets, uim)
        self.write_node(path, root)

    def _write_header(self, f):
        f.write('<?xml version="1.0" standalone="no"?> <!--*- mode: xml -*-->\n')
        doctype = None
        if self._version == 'libglade':
            doctype = "http://gazpacho.sicem.biz/gazpacho-0.1.dtd"

        if doctype:
            f.write('<!DOCTYPE glade-interface SYSTEM "%s">\n' % doctype)

    # FIXME: Should this really be exported
    def write_node(self, path, root):
        f = file(path, 'w')
        self._write_header(f)
        write_xml(f, root)
        f.close()

    def _create_root(self):
        if self._version == "libglade":
            tag = 'glade-interface'
        else:
            tag = 'interface'

        element = self._doc.createElement(tag)
        return self._doc.appendChild(element)

    def serialize_node(self, gadget):
        root = self._write_root()

        # save the UI Manager if needed
        widgets = gadget.project.uim.get_ui_widgets(gadget.widget)
        if widgets:
            uim_node = self._write_ui_manager(gadget.project.uim, widgets)
            if uim_node:
                root.appendChild(uim_node)

        # save the Model for TreeViews
        if isinstance(gadget.widget, gtk.TreeView):
            model = gadget.adaptor.get_model(gadget)
            self._write_model(root, model)

        root.appendChild(self._write_widget(gadget))

        return self._doc.documentElement

    def serialize(self, gadget, skip_external_references=False):

        if skip_external_references:
            self._skip_external_references = True
            self._all_widgets = get_all_widgets(gadget.widget)

        fp = io.StringIO()
        node = self.serialize_node(gadget)
        write_xml(fp, node)
        fp.seek(0)

        # reset context dependent states
        self._skip_external_references = False
        self._all_widgets = []

        return fp.read()

    def serialize_widgets(self, widgets, sizegroups, models, uim):
        fp = io.StringIO()
        root = self._write_root(widgets)
        self._write_sizegroups(root, sizegroups)
        for model in models:
            self._write_model(root, model)
        self._write_widgets(root, widgets, uim)
        write_xml(fp, root)
        fp.seek(0)

        return fp.read()

    def _get_requirements(self, widgets):
        # check what modules are the gadgets using

        modules = []
        for widget in widgets:
            gadget = Gadget.from_widget(widget)
            if gadget:
                libglade_module = gadget.adaptor.library.library_name
                if libglade_module and libglade_module not in modules:
                    modules.append(libglade_module)

        # the base module is not a requirement
        if 'base' in modules:
            modules.remove('base')

        return modules

    def _write_root(self, widgets=None, domain=None):
        root = self._create_root()

        if domain:
            root.setAttribute('domain', domain)

        # Disable require for now, see bug #344672
        if 0: #self._version == "libglade" and widgets:
            for module in self._get_requirements(widgets):
                n = self._doc.createElement('requires')
                n.setAttribute('lib', module)
                root.appendChild(n)

        return root

    def _create_object(self, class_name, name):
        if self._version == "gtkbuilder":
            tag = 'object'
        else:
            tag = 'widget'
        node = self._doc.createElement(tag)
        node.setAttribute('class', class_name)
        node.setAttribute('id', name)
        return node

    def _write_sizegroups(self, root, sizegroups):
        for sizegroup in sizegroups:
            node = self._create_object('GtkSizeGroup', sizegroup.name)
            root.appendChild(node)
            prop_node = self._doc.createElement('property')
            node.appendChild(prop_node)
            prop_node.setAttribute('name', 'mode')
            text = self._doc.createTextNode(enum_to_string(
                sizegroup.mode, enum=gtk.SizeGroupMode))
            prop_node.appendChild(text)

            # This needs to be cleaned up, ideally moved to sizegroup.py
            if self._version == 'gtkbuilder':
                widgets = self._doc.createElement('widgets')
                node.appendChild(widgets)
                for gadget in sizegroup.get_gadgets():
                    widget = self._doc.createElement('widget')
                    widget.setAttribute('name', gadget.name)
                    widgets.appendChild(widget)

    def _write_ui_manager(self, uim, widgets):
        """Create a XML node with the information of this UIManager

        Only the information about the widgets of this UIManager is
        actually saved.
        """

        action_groups = uim.get_action_groups()
        if not action_groups:
            return

        uim_node = self._create_object('GtkUIManager', uim.get_name())

        # first save action groups
        # XXX don't save all the action groups, only those ones
        # that are in use
        for action_group in action_groups:
            child_node = self._doc.createElement('child')
            uim_node.appendChild(child_node)
            child_node.appendChild(self._write_action_group(action_group))

        # Append uimanager
        gadgets = []
        for widget in widgets:
            if not isinstance(widget, (gtk.Toolbar, gtk.MenuBar)):
                continue
            gadget = Gadget.from_widget(widget)
            if gadget is None:
                raise AssertionError("There is no gadget for %s" % widget)
            gadgets.append(gadget)

        nodes = uim.save_ui_definitions(self._doc, gadgets, self._version)
        for ui_node in nodes:
            uim_node.appendChild(ui_node)

        return uim_node

    def _write_action_group(self, action_group):
        node = self._create_object('GtkActionGroup', action_group.name)

        # Sort all children, to keep the file format stabler
        action_names = action_group.get_action_names()
        action_names.sort()

        for action_name in action_names:
            child_node = self._doc.createElement('child')
            node.appendChild(child_node)
            action = action_group.get_action(action_name)
            child_node.appendChild(self._write_action(action))

        return node

    def _write_action(self, action):
        # XXX: Use a gadget and property wrappers

        action_node = self._create_object('GtkAction', action.name)

        default_label = None
        default_key = 0
        default_mask = None
        domain = None
        if action.stock_id:
            stock_info = gtk.stock_lookup(action.stock_id)
            if stock_info:
                (_, default_label, default_mask,
                 default_key, domain) = stock_info

        node = self._write_property('name', action.name)
        action_node.appendChild(node)

        # default_label is translated, so compare against the
        # untranslated version sent through dgettext()
        if default_label != dgettext(domain, action.label):
            node = self._write_property('label', action.label, True)
            action_node.appendChild(node)

        if action.label != action.short_label:
            node = self._write_property('short_label', action.short_label,
                                        True)
            action_node.appendChild(node)

        if action.is_important:
            node = self._write_property('is_important', 'True')
            action_node.appendChild(node)

        if action.tooltip:
            node = self._write_property('tooltip', action.tooltip, True)
            action_node.appendChild(node)

        if action.stock_id:
            node = self._write_property('stock_id', action.stock_id)
            action_node.appendChild(node)

        if action.callback:
            signal_node = self._write_signal('activate', action.callback)
            action_node.appendChild(signal_node)

        if action.accelerator and self._version != 'gtkbuilder':
            key, mask = gtk.accelerator_parse(action.accelerator)
            if key != default_key or mask != default_mask:
                node = self._write_property('accelerator',
                                            action.accelerator)
                action_node.appendChild(node)
        return action_node

    def _write_model(self, root, model):
        # <widget>
        #   <columns>
        #     <column type="...">
        #   </columns>
        # <widget/>

        model_node = self._create_object(model.get_type_name(),
                                         model.get_name())
        root.appendChild(model_node)

        # first we save the types
        column_type_names = model.get_column_type_names()
        if column_type_names:
            columns_node = self._doc.createElement('columns')
            model_node.appendChild(columns_node)
            for type_name in column_type_names:
                column_node = self._doc.createElement('column')
                column_node.setAttribute('type', type_name)
                columns_node.appendChild(column_node)

        # then the data
        store = model.get_model()
        if len(store):
            data_node = self._write_list_store_data(store,
                                                    len(column_type_names))
            model_node.appendChild(data_node)

    def _write_list_store_data(self, store, n_columns):
        # <data>
        #   <row>
        #     <col id="..">...</col>
        #   </row>
        # </data>

        data_node = self._doc.createElement('data')
        for row in store:
            row_node = self._doc.createElement('row')
            data_node.appendChild(row_node)

            for i in range(n_columns):
                col_node = self._doc.createElement('col')
                row_node.appendChild(col_node)
                col_node.setAttribute('id', str(i))

                data = row[i]
                if data is None:
                    text = ''
                else:
                    text = escape(str(row[i]))
                node = self._doc.createTextNode(text)
                col_node.appendChild(node)

        return data_node

    def _write_widgets(self, node, widgets, uim):
        ui_node = self._write_ui_manager(uim, widgets)
        if ui_node:
            node.appendChild(ui_node)

        # Append toplevel widgets. Each widget then takes care of
        # appending its children
        for widget in widgets:
            gadget = Gadget.from_widget(widget)
            if (gadget is None or
                not gadget.is_toplevel()):
                continue

            wnode = self._write_widget(gadget)
            node.appendChild(wnode)

        return node

    def _write_widget(self, gadget):
        """Serializes this gadget into a XML node and returns this node"""

        gadget.maintain_gtk_properties = True

        gadget.adaptor.save(gadget.project.context, gadget)

        # otherwise use the default saver
        node = self._write_basic_information(gadget)

        self._write_properties(node, gadget, child=False)
        for signals in gadget.get_all_signal_handlers():
            for signal in signals:
                signal_node = self._write_signal(signal.name, signal.handler,
                                                 signal.after, signal.object)
                node.appendChild(signal_node)

        # Children

        # We're not writing children when we have a constructor set
        if gadget.constructor:
            return node

        widget = gadget.widget
        children = gadget.get_children()
        if isinstance(widget, gtk.Table):
            table = widget
            def table_sort(a, b):
                res =  cmp(table.child_get_property(a, 'left-attach'),
                           table.child_get_property(b, 'left-attach'))
                if res == 0:
                    res = cmp(table.child_get_property(a, 'top-attach'),
                              table.child_get_property(b, 'top-attach'))
                return res
            children.sort(table_sort)

        # Boxes doesn't need to be sorted, they're already in the right order
        for child_widget in children:
            if isinstance(child_widget, Placeholder):
                child_node = self._write_placeholder(child_widget)
            elif isinstance(child_widget, gtk.CellRenderer):
                child_node = self._write_cell_renderer(child_widget,
                                                       gadget.widget)
            else:
                # if there is no gadget for this child
                # we don't save it. If your children are not being
                # saved you should create a gadget for them
                # in your Adaptor
                child_gadget = Gadget.from_widget(child_widget)
                if child_gadget is None:
                    continue
                child_node = self._write_child(child_gadget)

            node.appendChild(child_node)

        gadget.maintain_gtk_properties = False

        return node

    def _write_properties(self, parent_node, gadget, child):
        """
        @parent_node: the node of the parent, could be a widget node or a
           child node when setting packing properties
        @gadget:
        @child: boolean, if true write child properties, if false write normal
        """

        # <property name>...</property>
        # <property name>...</property>
        # ...
        properties = prop_registry.get_writable_properties(gadget.widget,
                                                           child)
        properties.sort(lambda a, b: cmp(a.name, b.name))

        for prop_type in properties:

            if prop_type.child:
                prop = gadget.get_child_prop(prop_type.name)
            else:
                prop = gadget.get_prop(prop_type.name)

            if isinstance(prop, ObjectType):
                if self._skip_external_references:
                    if prop.value not in self._all_widgets:
                        continue

            value = prop.save()
            if value == None:
                continue
            name = prop.name.replace('-', '_')
            translatable = False
            context = False
            comment = None
            if prop.is_translatable():
                translatable = True
                if prop.has_i18n_context:
                    context = True
                if prop.i18n_comment:
                    comment = prop.i18n_comment
            property_node = self._write_property(name, value, translatable,
                                                 context, comment)
            parent_node.appendChild(property_node)

    def _write_signal(self, name, handler, after=False, object=None):
        # <signal name="..." handler="..." after="..." object="..."/>
        signal_node = self._doc.createElement('signal')
        signal_node.setAttribute('name', name)
        signal_node.setAttribute('handler', handler)
        if after:
            signal_node.setAttribute('after', 'True')
        if object:
            signal_node.setAttribute('object', object)
        return signal_node

    def _write_basic_information(self, gadget):
        # <widget class="..." id=" constructor="">
        assert gadget.adaptor.type_name
        assert gadget.name, 'gadget %r is nameless' % gadget.widget

        # If name is set write it to the file
        if gadget.adaptor.name:
            type_name = gadget.adaptor.name
        else:
            type_name = gadget.adaptor.type_name

        node = self._create_object(type_name, gadget.name)
        if gadget.constructor:
            constructor = gadget.constructor
            node.setAttribute('constructor', constructor)
        return node

    def _write_child(self, child_gadget):
        # <child>
        #   <child internal-name="foo">
        # </child>

        child_node = self._doc.createElement('child')

        if child_gadget.internal_name is not None:
            child_node.setAttribute('internal-child',
                                    child_gadget.internal_name)

        child = self._write_widget(child_gadget)
        child_node.appendChild(child)

        # Append the packing properties
        packing_node = self._doc.createElement('packing')
        self._write_properties(packing_node, child_gadget, child=True)

        if packing_node.childNodes:
            child_node.appendChild(packing_node)

        return child_node

    def _write_placeholder(self, widget):
        # <child>
        #   <placeholder>
        # </child>

        child_node = self._doc.createElement('child')
        placeholder_node = self._doc.createElement('placeholder')
        child_node.appendChild(placeholder_node)

        # we need to write the packing properties of the placeholder.
        # otherwise the container gets confused when loading its
        # children
        node = self._write_placeholder_properties(widget)
        if node:
            child_node.appendChild(node)

        return child_node

    def _write_placeholder_properties(self, placeholder):
        # <placholder/>
        # <packing>
        #    <property>...</property>
        #    ....
        # </packing>

        parent = placeholder.get_parent()
        pspecs = gtk.container_class_list_child_properties(parent)
        if not pspecs:
            return
        packing_node = self._doc.createElement('packing')
        for pspec in pspecs:
            value = parent.child_get_property(placeholder, pspec.name)
            if value == pspec.default_value:
                continue
            prop_name = pspec.name.replace('-', '_')

            if gobject.type_is_a(pspec.value_type, gobject.TYPE_ENUM):
                v = enum_to_string(value, pspec)
            elif gobject.type_is_a(pspec.value_type, gobject.TYPE_FLAGS):
                v = flags_to_string(value, pspec)
            else:
                v = escape(str(value))

            prop_node = self._write_property(prop_name, v)
            packing_node.appendChild(prop_node)

        return packing_node

    def _write_property(self, name, value, translatable=False,
                        context=False, comment=False):
        # <property name="..."
        #           context="yes|no"
        #           translatable="yes|no">...</property>

        node = self._doc.createElement('property')

        # We should change each '-' by '_' on the name of the property
        # put the name="..." part on the <property ...> tag
        node.setAttribute('name', name)

        # Only write context and comment if translatable is
        # enabled, to mimic glade-2
        if translatable:
            node.setAttribute('translatable', 'yes')
            if context and self._version != 'gtkbuilder':
                node.setAttribute('context', 'yes')
            if comment:
                node.setAttribute('comment', comment)

        text = self._doc.createTextNode(escape(value))
        node.appendChild(text)
        return node

    def _write_cell_renderer(self, cell_renderer, column):
        child_node = self._doc.createElement('child')
        name = column.get_name_for_cell_renderer(cell_renderer)
        cell_node = self._create_object(gobject.type_name(cell_renderer), name)
        child_node.appendChild(cell_node)

        attributes_node = self._doc.createElement('attributes')
        child_node.appendChild(attributes_node)

        attributes = column.get_attributes(cell_renderer)
        for key, value in list(attributes.items()):
            attr_node = self._doc.createElement('attribute')
            attr_node.setAttribute('name', key)
            text = self._doc.createTextNode(escape(str(value)))
            attr_node.appendChild(text)
            attributes_node.appendChild(attr_node)

        return child_node


def get_all_widgets(widget):
    if isinstance(widget, Placeholder):
        return []

    widgets = [widget]
    if isinstance(widget, gtk.Container):
        for child in util.get_all_children(widget):
            widgets += get_all_widgets(child)
    return widgets
