# Copyright (C) 2005 Johan Dahlin
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

# TODO:
# Parser tags: atk, relation
# Document public API
# Parser subclass
# Improved unittest coverage
# Old style toolbars
# Require importer/resolver (gazpacho itself)
# GBoxed properties

import os
from gettext import textdomain, dgettext
from xml.parsers import expat

import gobject
import gtk
from gtk import gdk

from gazpacho.loader.custom import adapter_registry, flagsfromstring, \
     str2bool

__all__ = ['ObjectBuilder', 'ParseError']

def open_file(filename):
    if filename.endswith('.gz'):
        import gzip
        return gzip.GzipFile(filename, mode='rb')
    if filename.endswith('.bz2'):
        import bz2
        return bz2.BZ2File(filename, mode='rU')
    return open(filename, mode='rb')

class ParseError(Exception):
    pass

class Stack(list):
    push = list.append
    def peek(self):
        if self:
            return self[-1]

class BaseInfo:
    def __init__(self):
        self.data = ''

    def __repr__(self):
        return '<%s data=%r>' % (self.__class__.__name__,
                                 self.data)

class WidgetInfo(BaseInfo):
    def __init__(self, attrs, parent):
        BaseInfo.__init__(self)
        self.klass = str(attrs.get('class'))
        self.id = str(attrs.get('id'))
        self.constructor  = attrs.get('constructor')
        self.children = []
        self.properties = []
        self.attributes = {} # these are used for layout (e.g. cell renderers)
        self.signals = []
        self.uis = []
        self.accelerators = []
        self.parent = parent
        self.gobj = None
        # If it's a placeholder, used by code for unsupported widgets
        self.placeholder = False
        # these attributes are useful for models:
        self.columns = []
        self.rows = []

    def is_internal_child(self):
        if self.parent and self.parent.internal_child:
            return True
        return False

    def __repr__(self):
        return '<WidgetInfo %s>' % (self.id)

class ChildInfo(BaseInfo):
    def __init__(self, attrs, parent):
        BaseInfo.__init__(self)
        self.type = attrs.get('type')
        self.internal_child = attrs.get('internal-child')
        self.properties = []
        self.packing_properties = []
        self.attributes = {}
        self.placeholder = False
        self.parent = parent
        self.widget = None

    def __repr__(self):
        return '<ChildInfo containing a %s>' % (self.widget)

class PropertyInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        self.name = str(attrs.get('name'))
        self.translatable = str2bool(attrs.get('translatable', 'no'))
        self.context = str2bool(attrs.get('context', 'no'))
        self.agent = attrs.get('agent') # libglade
        self.comments = attrs.get('comments')

    def __repr__(self):
        return '<PropertyInfo of type %s=%r>' % (self.name, self.data)

class SignalInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        self.name = attrs.get('name')
        self.handler = attrs.get('handler')
        self.after = str2bool(attrs.get('after', 'no'))
        self.object = attrs.get('object')
        self.last_modification_time = attrs.get('last_modification_time')
        self.gobj = None

class AcceleratorInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        self.key = gdk.keyval_from_name(attrs.get('key'))
        self.modifiers = flagsfromstring(attrs.get('modifiers'),
                                         flags=gdk.ModifierType)
        self.signal = str(attrs.get('signal'))

class UIInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        self.id = attrs.get('id')
        self.filename = attrs.get('filename')
        self.merge = str2bool(attrs.get('merge', 'yes'))

class SizeGroupInfo(BaseInfo):
    def __init__(self, name):
        BaseInfo.__init__(self)
        self.name = name
        self.widgets = []

class AttributeInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        self.name = str(attrs.get('name'))

class ColumnsInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        self.columns = []

class ColumnInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        type_name = str(attrs.get('type'))
        try:
            self.type = gobject.type_from_name(type_name)
        except RuntimeError:
            raise ParseError('the type %s is not a valid GType' % type_name)

class RowInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        self.cols = []

class ColInfo(BaseInfo):
    def __init__(self, attrs):
        BaseInfo.__init__(self)
        try:
            self.id = int(attrs.get('id'))
        except ValueError:
            raise ParseError('id attribute must be integer')

class ExpatParser(object):
    def __init__(self, builder):
        self._builder = builder
        self.requires = []
        self._stack = Stack()
        self._state_stack = Stack()
        self._ui_state = False
        self._widgets_state = False
        self._sizegroups = []
        self._parser = expat.ParserCreate()
        self._parser.buffer_text = True
        self._parser.StartElementHandler = self._handle_startelement
        self._parser.EndElementHandler = self._handle_endelement
        self._parser.CharacterDataHandler = self._handle_characterdata

    # Public API
    def parse_file(self, filename):
        fp = open_file(filename)
        try:
            self._parser.ParseFile(fp)
        except expat.ExpatError as e:
            raise ParseError(e)

    def parse_stream(self, buf):
        try:
            self._parser.Parse(buf)
        except expat.ExpatError as e:
            raise ParseError(e)

    def _build_ui(self, name, attrs):
        extra = ''
        for attr, value in list(attrs.items()):
            extra += " %s=\"%s\"" % (attr, value)

        ui = self._stack.peek()
        ui.data += "<%s%s>" % (name, extra)

    # Expat callbacks
    def _handle_startelement(self, name, attrs):
        if self._ui_state:
            self._build_ui(name, attrs)
            return
        self._state_stack.push(name)
        name = name.replace('-', '_')
        func = getattr(self, '_start_%s' % name, None)
        if func:
            item = func(attrs)
            self._stack.push(item)

    def _handle_endelement(self, name):
        if self._ui_state:
            ui = self._stack.peek()
            if name != "ui":
                ui.data += "</%s>" % name
                return
            elif not ui.data.startswith("<ui>"):
                ui.data = "<ui>%s</ui>" % ui.data

        self._state_stack.pop()
        name = name.replace('-', '_')
        func = getattr(self, '_end_%s' % name, None)
        if func:
            item = self._stack.pop()
            func(item)

    def _handle_characterdata(self, data):
        info = self._stack.peek()
        if info:
            info.data += str(data)

    # Tags
    def _start_glade_interface(self, attrs):
        # libglade extension, add a domain argument to the interface
        if 'domain' in attrs:
            self._builder._domain = str(attrs['domain'])
        self._builder._version = "libglade"

    def _end_glade_interface(self, obj):
        pass

    def _start_interface(self, attrs):
        # libglade extension, add a domain argument to the interface
        if 'domain' in attrs:
            self._builder._domain = str(attrs['domain'])
        self._builder._version = "gtkbuilder"

    def _end_interface(self, attrs):
        pass

    def _start_requires(self, attrs):
        self.requires.append(attrs)

    def _end_requires(self, obj):
        pass

    def _start_signal(self, attrs):
        if not 'name' in attrs:
            raise ParseError("<signal> needs a name attribute")
        if not 'handler' in attrs:
            raise ParseError("<signal> needs a handler attribute")
        return SignalInfo(attrs)

    def _end_signal(self, signal):
        obj = self._stack.peek()
        obj.signals.append(signal)

    def _start__common(self, attrs):
        if not 'class' in attrs:
            raise ParseError("<widget> needs a class attribute")
        if not 'id' in attrs:
            raise ParseError("<widget> needs an id attribute")

        return WidgetInfo(attrs, self._stack.peek())

    def _start_widget(self, attrs):
        if self._widgets_state:
            obj = self._stack.peek()
            obj.widgets.append(str(attrs.get('name')))
            return
        else:
            if self._builder._version == 'gtkbuilder':
                raise ParseError("Unknown tag: widget")
        return self._start__common(attrs)

    def _start_object(self, attrs):
        if self._builder._version == 'libglade':
            raise ParseError("Unknown tag: object")
        return self._start__common(attrs)

    def _end__common(self, obj):
        obj.parent = self._stack.peek()

        if not obj.gobj:
            obj.gobj = self._builder._build_phase1(obj)

        self._builder._build_phase2(obj)

        if obj.parent:
            obj.parent.widget = obj.gobj

    def _end_widget(self, attrs):
        if self._widgets_state:
            return
        return self._end__common(attrs)

    def _end_object(self, attrs):
        return self._end__common(attrs)

    def _start_child(self, attrs):
        obj = self._stack.peek()
        if not obj.gobj:
            obj.gobj = self._builder._build_phase1(obj)

        return ChildInfo(attrs, parent=obj)

    def _end_child(self, child):
        obj = self._stack.peek()
        obj.children.append(child)

    def _start_property(self, attrs):
        if not 'name' in attrs:
            raise ParseError("<property> needs a name attribute")
        return PropertyInfo(attrs)

    def _end_property(self, prop):
        if prop.agent and prop.agent not in ('libglade', 'gazpacho'):
            return

        # gettext cannot really handle empty strings, so we need to filter
        # them out, otherwise we'll get the po header as the content!
        # Note that we should not write properties with empty strings from
        # the start, but that is another bug
        if prop.translatable and prop.data:
            if not self._builder._ignore_domain:
                prop.data = dgettext(self._builder._domain, prop.data)

        obj = self._stack.peek()

        property_type = self._state_stack.peek()
        if property_type == 'widget' or property_type == 'object':
            obj.properties.append(prop)
        elif property_type == 'packing':
            obj.packing_properties.append(prop)
        else:
            raise ParseError("property must be a node of widget or packing")

    def _start_ui(self, attrs):
        if self._builder._version != 'gtkbuilder':
            if not 'id' in attrs:
                raise ParseError("<ui> needs an id attribute")
        self._ui_state = True
        return UIInfo(attrs)

    def _end_ui(self, ui):
        self._ui_state = False
        if not ui.data or ui.filename:
            raise ParseError("<ui> needs CDATA or filename")

        obj = self._stack.peek()
        obj.uis.append(ui)

    def _start_placeholder(self, attrs):
        pass

    def _end_placeholder(self, placeholder):
        obj = self._stack.peek()
        obj.placeholder = True

    def _start_accelerator(self, attrs):
        if not 'key' in attrs:
            raise ParseError("<accelerator> needs a key attribute")
        if not 'modifiers' in attrs:
            raise ParseError("<accelerator> needs a modifiers attribute")
        if not 'signal' in attrs:
            raise ParseError("<accelerator> needs a signal attribute")
        return AcceleratorInfo(attrs)

    def _end_accelerator(self, accelerator):
        obj = self._stack.peek()
        obj.accelerators.append(accelerator)

    def _start_widgets(self, attrs):
        self._widgets_state = True
        obj = self._stack.peek()
        return SizeGroupInfo(obj.id)

    def _end_widgets(self, obj):
        self._builder._add_sizegroup_widgets(obj.name, obj.widgets)

    def _start_attribute(self, attrs):
        if not 'name' in attrs:
            raise ParseError("<attribute> needs a name attribute")
        return AttributeInfo(attrs)

    def _end_attribute(self, attribute):
        obj = self._stack.peek()

        try:
            data = int(attribute.data)
        except ValueError:
            raise ParseError("attribute value must be an integer")

        property_type = self._state_stack.peek()
        if property_type == 'attributes':
            obj.attributes[attribute.name] = data
        else:
            raise ParseError("attribute must be a node of <attributes>")

    def _start_column(self, attrs):
        if not 'type' in attrs:
            raise ParseError("<column> needs a type attribute")
        return ColumnInfo(attrs)

    def _end_column(self, column):
        obj = self._stack.peek()
        parent_type = self._state_stack.peek()
        if parent_type == 'columns':
            obj.columns.append(column)
        else:
            raise ParseError("column must be a node of <columns>")

    def _start_row(self, attrs):
        return RowInfo(attrs)

    def _end_row(self, row):
        obj = self._stack.peek()
        parent_type = self._state_stack.peek()
        if parent_type == 'data':
            obj.rows.append(row)
        else:
            raise ParseError("row must be a node of <data>")

    def _start_col(self, attrs):
        if not 'id' in attrs:
            raise ParseError("<col> needs an id attribute")
        return ColInfo(attrs)

    def _end_col(self, col):
        obj = self._stack.peek()
        parent_type = self._state_stack.peek()
        if parent_type == 'row':
            obj.cols.append(col)
        else:
            raise ParseError("col must be a node of <row>")

class ObjectBuilder:
    def __init__(self, filename='', buffer=None, root=None, placeholder=None,
                 custom=None, domain=None, ignore_domain=False):
        if ((not filename and not buffer) or
            (filename and buffer)):
            raise TypeError("need a filename or a buffer")

        self._filename = filename
        self._buffer = buffer
        self._root = root
        self._placeholder = placeholder
        self._custom = custom
        self._domain = domain
        self._ignore_domain = ignore_domain

        # maps the classes of widgets that failed to load to lists of
        # widget ids
        self._unsupported_widgets = {}

        # name -> GObject
        self._widgets = {}
        self._signals = []
        # GObject -> Constructor
        self._constructed_objects = {}
        # ui definition name -> UIMerge, see _mergeui
        self._uidefs = {}
        # ui definition name -> constructor name (backwards compatibility)
        self._uistates = {}
        self._tooltips = gtk.Tooltip()
        #self._tooltips.enable()
        self._focus_widget = None
        self._default_widget = None
        self._toplevel = None
        self._accel_group = None
        self._delayed_properties = {}
        self._internal_children = {}
        self._sizegroup_widgets = {}

        # Public
        self.toplevels = []
        self.sizegroups = []

        # If domain is not specified, fetch the default one by
        # calling textdomain() without arguments
        if not domain:
            domain = textdomain()
            # messages is the default domain, ignore it
            if domain == 'messages':
                domain = None

        self._parser = ExpatParser(self)
        if filename:
            self._parser.parse_file(filename)
        elif buffer:
            self._parser.parse_stream(buffer)
        self._parse_done()

    def __len__(self):
        return len(self._widgets)

    def __bool__(self):
        return True

    # Public API

    def get_domain(self):
        return self._domain

    def get_version(self):
        return self._version

    def get_widget(self, widget):
        return self._widgets.get(widget)

    def get_widgets(self):
        return list(self._widgets.values())

    def get_unsupported_widgets(self):
        """
        Get a dict of the widgets that could not be loaded because
        they're not supported. The dict maps the class of the widget
        to a list of widget ids.

        @return: the unsupported widgets
        @rtype: dict
        """
        return self._unsupported_widgets

    def signal_autoconnect(self, obj):
        for gobj, name, handler_name, after, object_name in self.get_signals():
            # Firstly, try to map it as a dictionary
            try:
                handler = obj.get(handler_name)
            except (AttributeError, TypeError):
                # If it fails, try to map it to an attribute
                handler = getattr(obj, handler_name, None)
            if not handler:
                continue

            if object_name:
                other = self._widgets.get(object_name)
                if after:
                    gobj.connect_object_after(name, handler, other)
                else:
                    gobj.connect_object(name, handler, other)
            else:
                if after:
                    gobj.connect_after(name, handler)
                else:
                    gobj.connect(name, handler)

    def show_windows(self):
# Doesn't quite work, disabled for now
#         # First set focus, warn if more than one is focused
#         toplevel_focus_widgets = []
#         for widget in self.get_widgets():
#             if not isinstance(widget, gtk.Widget):
#                 continue

#             if widget.get_data('gazpacho::is-focus'):
#                 toplevel = widget.get_toplevel()
#                 name = toplevel.get_name()
#                 if name in toplevel_focus_widgets:
#                     print ("Warning: Window %s has more than one "
#                            "focused widget" % name)
#                 toplevel_focus_widgets.append(name)

        # At last, display all of the visible windows
        for toplevel in self.toplevels:
            if not isinstance(toplevel, gtk.Window):
                continue
            value = toplevel.get_data('gazpacho::visible')
            toplevel.set_property('visible', value)

    def get_internal_child(self, gobj):
        if not gobj in self._internal_children:
            return []
        return self._internal_children[gobj]

    def get_internal_children(self):
        return self._internal_children

    # Adapter API

    def add_signal(self, gobj, name, handler, after=False, sig_object=None):
        self._signals.append((gobj, name, handler, after, sig_object))

    def get_signals(self):
        return self._signals

    def find_resource(self, filename):
        dirname = os.path.dirname(self._filename)
        path = os.path.join(dirname, filename)
        if os.access(path, os.R_OK):
            return path

    def get_ui_definitions(self):
        return [(name, info.data, info.merge_id)
                    for name, info in list(self._uidefs.items())]

    def get_constructor(self, gobj):
        return self._constructed_objects[gobj]

    def ensure_accel(self):
        if not self._accel_group:
            self._accel_group = gtk.AccelGroup()
            if self._toplevel:
                self._toplevel.add_accel_group(self._accel_group)
        return self._accel_group

    def add_delayed_property(self, obj_id, pspec, value):
        self._delayed_properties.setdefault(obj_id, []).append((pspec, value))

    # Private

    def _setup_signals(self, gobj, signals):
        for signal in signals:
            self.add_signal(gobj, signal.name, signal.handler,
                           signal.after, signal.object)

    def _setup_accelerators(self, widget, accelerators):
        if not accelerators:
            return

        accel_group = self.ensure_accel()
        widget.set_data('gazpacho::accel-group', accel_group)
        for accelerator in accelerators:
            widget.add_accelerator(accelerator.signal,
                                   accel_group,
                                   accelerator.key,
                                   accelerator.modifiers,
                                   gtk.ACCEL_VISIBLE)

    def _apply_delayed_properties(self):
        for obj_id, props in list(self._delayed_properties.items()):
            widget = self._widgets.get(obj_id)
            if widget is None:
                raise AssertionError

            type_name = gobject.type_name(widget)
            adapter = adapter_registry.get_adapter(widget, type_name, self)

            prop_list = []
            for pspec, value in props:
                if gobject.type_is_a(pspec.value_type, gobject.GObject):
                    other = self._widgets.get(value)
                    if other is None:
                        raise ParseError(
                            "property %s of %s refers to object %s which "
                            "does not exist" % (pspec.name, obj_id,value))
                    prop_list.append((pspec.name, other))
                else:
                    raise NotImplementedError(
                        "Only delayed object properties are "
                        "currently supported")

            adapter.set_properties(widget, prop_list)

    def _merge_ui(self, uimanager_name, name,
                  filename='', data=None, merge=True):
        #uimanager = self._widgets[uimanager_name]
        uimanager = gtk.UIManager()
        if merge:
            if filename:
                filename = self.find_resource(filename)
                # XXX Catch GError
                merge_id = uimanager.add_ui_from_file(filename)
            elif data:
                # XXX Catch GError
                merge_id = uimanager.add_ui_from_string(data)
            else:
                raise AssertionError
        else:
            merge_id = -1

        class UIMerge:
            def __init__(self, uimanager, filename, data, merge_id):
                self.uimanager = uimanager,
                self.filename = filename
                self.data = data
                self.merge_id = merge_id

        current = self._uidefs.get(name)
        if current:
            current.merge_id = merge_id
        else:
            self._uidefs[name] = UIMerge(uimanager, filename, data,
                                         merge_id)

        # Backwards compatibility
        self._uistates[name] = uimanager_name

    def _uimanager_construct(self, uimanager_name, obj_id):
        uimanager = gtk.UIManager() #self._widgets[uimanager_name]
        widget = uimanager.get_widget('ui/' + obj_id)
        if widget is not None:
            setattr(widget, 'uimanagername', uimanager_name)
        else:
            # XXX: untested code
            uimanager_name = self._uistates.get(obj_id)
            if not uimanager_name:
                #raise AssertionError
                return
            uimanager = self._widgets[uimanager_name]

        return widget

    def _find_internal_child(self, obj):
        child = None
        childname = str(obj.parent.internal_child)
        parent = obj.parent
        while parent:
            if isinstance(parent, ChildInfo):
                parent = parent.parent
                continue

            gparent = parent.gobj
            if not gparent:
                break

            adapter = adapter_registry.get_adapter(gparent, parent.klass, self)
            child = adapter.find_internal_child(gparent, childname)
            if child is not None:
                break

            parent = parent.parent

        if child is not None:
            children = self._internal_children.setdefault(gparent, [])
            children.append((childname, child))
            # Childname is attribute name, which we use to find the child
            # in the parent widget.
            # obj.id stores the real name, it needs to be set manually here
            # since we're not calling the widget adapters constructor
            child.set_name(obj.id)
            child.set_data('gazpacho::internal-child-name', childname)
        return child

    def _create_custom(self, obj):
        kwargs = dict(name=obj.id)
        for prop in obj.properties:
            prop_name = prop.name
            if prop_name in ('string1', 'string2',
                             'creation_function',
                             'last_modification_time'):
                kwargs[prop_name] = prop.data
            elif prop_name in ('int1', 'int2'):
                kwargs[prop_name] = int(prop.data)

        if not self._custom:
            return gtk.Label('<Custom: %s>' % obj.id)
        elif callable(self._custom):
            func = self._custom
            return func(**kwargs)
        else:
            func_name = kwargs['creation_function']
            try:
                func = self._custom[func_name]
            except (TypeError, KeyError, AttributeError):
                func = getattr(self._custom, func_name, None)

            return func(name=obj.id,
                        string1=kwargs.get('string1', None),
                        string2=kwargs.get('string2', None),
                        int1=kwargs.get('int1', None),
                        int2=kwargs.get('int2', None))

    def _create_placeholder(self, obj=None):
        if not self._placeholder:
            return

        if not obj:
            name = 'unknown'
        else:
            name = obj.id

        return self._placeholder(name)

    def _add_widget(self, object_id, gobj):
        #gobj.set_data('gazpacho.objectid', object_id)
        setattr(gobj, 'objectid', object_id)
        self._widgets[object_id] = gobj.objectid

    def _build_phase1(self, obj):
        assert obj.gobj is None, obj.id

        root = self._root
        if root and root != obj.id:
            return

        if obj.klass == 'Custom':
            gobj = self._create_custom(obj)
            if gobj:
                self._add_widget(obj.id, gobj)
            return gobj

        try:
            gtype = gobject.type_from_name(obj.klass)
        except RuntimeError:
            self._unsupported_widgets.setdefault(obj.klass, []).append(obj.id)
            obj.placeholder = True
            return self._create_placeholder(obj)

        adapter = adapter_registry.get_adapter(gtype, obj.klass, self)

        construct, normal = adapter.get_properties(gtype,
                                                   obj.id,
                                                   obj.properties)
        if obj.is_internal_child():
            gobj = self._find_internal_child(obj)
        elif obj.constructor:
            if obj.constructor in self._widgets:
                gobj = self._uimanager_construct(obj.constructor, obj.id)
                constructor = obj.constructor
            # Backwards compatibility
            elif obj.constructor in self._uistates:
                constructor = self._uistates[obj.constructor]
                gobj = self._uimanager_construct(constructor, obj.id)
            else:
                raise ParseError("constructor %s for object %s could not "
                                 "be found" % (obj.constructor, obj.id))
            self._constructed_objects[gobj] = self._widgets[constructor]
        else:
            gobj = adapter.construct(obj.id, gtype, construct)

        if gobj:
            self._add_widget(obj.id, gobj)

            if isinstance(gobj, gtk.ListStore):
                adapter.set_column_types(gobj, obj.columns)
                adapter.fill(gobj, obj.rows)

            adapter.set_properties(gobj, normal)

            # This is a little tricky
            # We assume the default values for all these are nonzero, eg
            # either False or None
            # We also need to handle the case when we have two labels, if we
            # do we respect the first one. This is due to a bug in the save code
            for propinfo in obj.properties:
                key = 'i18n_is_translatable_%s' % propinfo.name
                if not (hasattr(gobj, key) and propinfo.translatable):
                    setattr(gobj, key, propinfo.translatable)

                key = 'i18n_has_context_%s' % propinfo.name
                if not hasattr(gobj, key) and propinfo.context:
                    setattr(gobj, key, propinfo.context)

                # XXX: Rename to i18n_comments
                key = 'i18n_comment_%s' % propinfo.name
                if not hasattr(gobj, key) and propinfo.comments:
                    setattr(gobj, key, propinfo.comments)

        return gobj

    def _build_phase2(self, obj):
        # If we have a root set, we don't want to construct all
        # widgets, filter out unwanted here
        root = self._root
        if root and root != obj.id:
            return

        # Skip this step for placeholders, so we don't
        # accidentally try to pack something into unsupported widgets
        if obj.placeholder:
            return

        gobj = obj.gobj
        if not gobj:
            return

        adapter = adapter_registry.get_adapter(gobj, obj.klass, self)

        for child in obj.children:
            self._pack_child(adapter, gobj, child)

        self._setup_signals(gobj, obj.signals)
        self._setup_accelerators(gobj, obj.accelerators)

        # Toplevels
        if not obj.parent:
            if isinstance(gobj, gtk.UIManager):
                for ui in obj.uis:
                    self._merge_ui(obj.id,
                                   ui.id, ui.filename, ui.data, ui.merge)
                    self.accelgroup = gobj.get_accel_group()
            elif isinstance(gobj, gtk.Window):
                self._set_toplevel(gobj)
            self.toplevels.append(gobj)

    def _pack_child(self, adapter, gobj, child):

        if child.placeholder:
            widget = self._create_placeholder()
            if not widget:
                return
        elif child.widget:
            widget = child.widget
        else:
            return

        if child.internal_child:
            gobj = child.parent.gobj
            name = child.parent.id
            if isinstance(gobj, gtk.Widget):
                gobj.set_name(name)
            self._add_widget(name, gobj)
            return

        # 5) add child
        try:
            adapter.add(gobj,
                        widget,
                        child.packing_properties,
                        child.type)
        except NotImplementedError:
            raise ParseError(
                '%s of type %s has children, but its not supported' % (
                child.parent.id,
                gobject.type_name(gobj)))

        if isinstance(gobj, gtk.CellLayout):
            adapter.set_cell_renderer_attributes(gobj, widget, child.attributes)

    def _attach_accel_groups(self):
        # This iterates of all objects constructed by a gtk.UIManager
        # And attaches an accelgroup to the toplevel window of them
        for widget, constructor in list(self._constructed_objects.items()):
            if not isinstance(constructor, gtk.UIManager):
                continue
            toplevel = widget.get_toplevel()
            if not isinstance(toplevel, gtk.Window):
                continue
            accel_group = constructor.get_accel_group()
            if not accel_group in gtk.accel_groups_from_object(toplevel):
                toplevel.add_accel_group(accel_group)

    def _add_sizegroup_widgets(self, group_name, widget_names):
        self._sizegroup_widgets[group_name] = widget_names

    def _setup_sizegroups(self):
        # gtkbuilder way
        for group_name, widget_names in list(self._sizegroup_widgets.items()):
            for widget_name in widget_names:
                widget = self._widgets[widget_name]
                widget.set_data('gazpacho::sizegroup', group_name)

        for widget in list(self._widgets.values()):
            # Collect all the sizegroups
            if isinstance(widget, gtk.SizeGroup):
                self.sizegroups.append(widget)
                continue

            # And setup the widgets which has a sizegroup
            if not isinstance(widget, gtk.Widget):
                continue

            group_name = widget.get_data('gazpacho::sizegroup')
            if group_name is None:
                continue
            group = self.get_widget(group_name)
            if group is None:
                raise ParseError("sizegroup %s does not exist" %
                                 group_name)
            group.add_widget(widget)

            # Keep a list of widgets inside the sizegroup.
            # Perhaps GTK+ should provide an api for this.
            sgwidgets = group.get_data('gazpacho::sizegroup-widgets')
            if sgwidgets is None:
                sgwidgets = []
                group.set_data('gazpacho::sizegroup-widgets', sgwidgets)
            sgwidgets.append(widget)

    def _parse_done(self):
        self._apply_delayed_properties()
        self._attach_accel_groups()
        self._setup_sizegroups()
        self.show_windows()

    def _set_toplevel(self, window):
        if self._focus_widget:
            self._focus_widget.grab_focus()
            self._focus_widget = None
        if self._default_widget:
            if self._default_widget.flags() & gtk.CAN_DEFAULT:
                self._default_widget.grab_default()
            self._default_widget = None
        if self._accel_group:
            self._accel_group = None

        # the window should hold a reference to the tooltips object
        window.set_data('gazpacho::tooltips', self._tooltips)
        self._toplevel = window

if __name__ == '__main__':
    import sys
    ob = ObjectBuilder(filename=sys.argv[1])
    for toplevel in ob.toplevels:
        if not isinstance(toplevel, gtk.Window):
            continue
        toplevel.connect('delete-event', gtk.main_quit)
        toplevel.show_all()

    gtk.main()
