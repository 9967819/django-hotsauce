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
import sys
PY3K = sys.version_info[0] == 3
import gi
import gobject
import gtk
from gtk import gdk

def enumfromstring(value_name, pspec=None, enum=None):
    if not value_name:
        return 0

    try:
        value = int(value_name)
    except ValueError:
        if pspec:
            enum_class = pspec.enum_class
            if enum_class is None:
                return 0
        elif enum:
            enum_class = enum
        else:
            raise ValueError("Need pspec or enm")

        for value, enum in list(enum_class.__enum_values__.items()):
            if value_name in (enum.value_name, enum.value_nick):
                return value

    raise ValueError("Invalid enum value: %r" % value_name)

def flagsfromstring(value_name, pspec=None, flags=None):
    if not value_name:
        return 0

    try:
        return int(value_name)
    except ValueError:
        pass

    value_names = [v.strip() for v in value_name.split('|')]

    if pspec:
        flags_class = pspec.flags_class
    elif flags:
        flags_class = flags
    else:
        raise ValueError("need pspec or flags")

    flag_values = flags_class.__flags_values__
    new_value = 0
    for mask, flag in list(flag_values.items()):
        if (flag.value_names[0] in value_names or
            flag.value_nicks[0] in value_names):
            new_value |= mask

    return new_value

def valuefromstringsimpletypes(gtype, string):
    if gtype in (gobject.TYPE_CHAR, gobject.TYPE_UCHAR):
        value = string[0]
    elif gtype == gobject.TYPE_BOOLEAN:
        value = str2bool(string)
    elif gtype in (gobject.TYPE_INT, gobject.TYPE_UINT):
        value = int(string)
    elif gtype in (gobject.TYPE_LONG, gobject.TYPE_ULONG):
        value = int(string)
    elif gtype in (gobject.TYPE_FLOAT, gobject.TYPE_DOUBLE):
        value = float(string)
    elif gtype == gobject.TYPE_STRING:
        value = string
    elif gobject.type_is_a(gtype, gobject.TYPE_PYOBJECT):
        value = string
    elif gobject.type_is_a(gtype, gobject.GBoxed):
        print ('TODO: boxed')
        value = None
    else:
        raise TypeError("type %r is unknown" % gtype)

    return value

def str2bool(value):
    return value[0].lower() in ('t', 'y') or value == '1'

def get_child_pspec_from_name(gtype, name):
    if gtk.pygtk_version < (2, 10, 0):
        pspecs = gtk.container_class_list_child_properties(gtype)
    else:
        pspecs = gtype.list_child_properties()

    for pspec in pspecs:
        if pspec.name == name:
            return pspec

def get_pspec_from_name(gtype, name):
    for pspec in gobject.list_properties(gtype):
        if pspec.name == name:
            return pspec

class AdapterMeta(type):
    def __new__(mcs, name, bases, dict):
        t = type.__new__(mcs, name, bases, dict)
        t.add_adapter()
        return t

class IObjectAdapter:
    """This interface is used by the loader to build
    a custom object.

    object_type is a GType representing which type we can construct
    """
    object_type = None

    def construct(self, name, properties):
        """constructs a new type of type gtype
        name:  string representing the type name
        gtype: gtype of the object to be constructed
        properties: construct properties
        """
        pass

    def add(self, gobj, child, properties, type):
        """Adds a child to gobj with properties"""
        pass

    def get_properties(self, gtype, obj_id, properties):
        pass

    def set_properties(self, gobj, properties):
        pass

    def prop_set_NAME(self, widget, value_string):
        """
        Sets the property NAME for widget, note that you have to convert
        from a string manully"""
        pass

    def find_internal_child(self, gobj, name):
        """Returns an internal child"""

    def get_internal_child_name(self, gobj, child):
        """
        Returns the name of a widget, as an internal child or None
        if it cannot be found
        """

class Adapter(object, metaclass=AdapterMeta):
    _adapters = []
    _properties = {}

    def __init__(self, build):
        self._build = build

    def get_raw_property(self, object, name):
        object_id = object.get_data('gazpacho::object-id')
        if not object_id in self._properties:
            raise KeyError(object_id)
        return self._properties[object_id][name]

    def add_adapter(cls):
        if cls.__name__ != 'Adapter':
            cls._adapters.append(cls)
    add_adapter = classmethod(add_adapter)

    def get_adapters(cls):
        return cls._adapters
    get_adapters = classmethod(get_adapters)

class AdapterRegistry:
    def __init__(self):
        # GObject typename -> adapter instance
        self._adapters = {}

        for adapter in Adapter.get_adapters():
            self.register_adapter(adapter)

    def _add_adapter(self, name, adapter):
        self._adapters[name] = adapter

    def register_adapter(self, adapter):
        adict = adapter.__dict__
        # Do not register abstract adapters
        if 'object_type' in adict:
            object_type = adict.get('object_type')
            if type(object_type) != tuple:
                object_type = object_type,

            for klass in object_type:
                self._add_adapter(gobject.type_name(klass), adapter)
        elif 'object_name' in adict:
            self._add_adapter(adict.get('object_name'), adapter)

    def get_adapter(self, gobj, type_name=None, build=None):
        # Name is optional, for performance reasons we want
        # to send it as often as we can, normally it's already
        # known at the callsite.
        if type_name == None:
            type_name = gobject.type_name(gobj)
        orig_name = type_name

        while True:
            adapter = self._adapters.get(type_name)
            if adapter:
                # Store a reference for the adapter, to make the
                # next lookup faster
                self._adapters[orig_name] = adapter
                return adapter(build)

            gobj = gobject.type_parent(gobj)
            type_name = gobject.type_name(gobj)

class GObjectAdapter(Adapter):
    object_type = gobject.GObject
    child_names = []
    def construct(self, name, gtype, properties):
        # Due to a bug in gobject.new() we only send in construct
        # only properties here, the rest are set normally
        gobj = gobject.new(gtype, **properties)
        return gobj

    def get_properties(self, gtype, obj_id, properties):
        return self._getproperties(gtype, obj_id, properties)

    def set_properties(self, gobj, properties):
        prop_names = []
        for name, value in properties:
            #print '%s.%s = %r' % (gobject.type_name(gobj), name, value)
            func_name = 'prop_set_%s' % name.replace('-', '_')
            func = getattr(self, func_name, None)
            if func:
                func(gobj, value)
            else:
                gobj.set_property(name, value)

            prop_names.append(name)

        #gobj.set_data('gobject.changed_properties', prop_names)
        setattr(gobj, 'changed_properties', prop_names)

    def _getproperties(self, gtype, obj_id, properties, child=False):
        if child:
            get_pspec = get_child_pspec_from_name
        else:
            get_pspec = get_pspec_from_name

        propdict = self._properties
        if obj_id not in propdict:
            props = propdict[obj_id] = {}
        else:
            props = propdict[obj_id]

        construct = {}
        normal = []
        for prop in properties:
            propname = prop.name.replace('_', '-')
            #full = '%s::%s' % (gobject.type_name(gtype), propname)
            props[prop.name] = prop.data
            if hasattr(self, 'prop_set_%s' % prop.name):
                normal.append((prop.name, prop.data))
                continue

            pspec = get_pspec(gtype, propname)
            if not pspec:
                print(('Unknown property: %s:%s (id %s)' %
                       (gobject.type_name(gtype),
                        prop.name,
                        obj_id)))
                continue

            try:
                value = self._valuefromstring(obj_id, pspec, prop.data)
            except ValueError:
                print(("Convertion failed for %s:%s (id %s), "
                       "expected %s but found %r" %
                       (gobject.type_name(gtype),
                        prop.name,
                        obj_id,
                        gobject.type_name(pspec.value_type),
                        prop.data)))
                continue

            # Could not
            if value is None:
                continue

            if pspec.flags & gobject.PARAM_CONSTRUCT_ONLY != 0:
                construct[pspec.name] = value
            else:
                normal.append((pspec.name, value))

        if child:
            assert not construct
            return normal

        return construct, normal

    def _valuefromstring(self, obj_id, pspec, string):
        # This is almost a 1:1 copy of glade_xml_set_value_from_string from
        # libglade.
        prop_type = pspec.value_type

        if (prop_type in (gobject.TYPE_INT, gobject.TYPE_UINT)
            and gobject.type_name(pspec) == 'GParamUnichar'):
            value = str(string and string[0] or "")
            return value

        try:
            value = valuefromstringsimpletypes(prop_type, string)
        except TypeError:
            pass # it's ok if we fail so far, we'll try other types
        else:
            return value

        if gobject.type_is_a(prop_type, gobject.TYPE_ENUM):
            value = enumfromstring(string, pspec)
        elif gobject.type_is_a(prop_type, gobject.TYPE_FLAGS):
            value = flagsfromstring(string, pspec)
        elif gobject.type_is_a(prop_type, gobject.GObject):
            if gobject.type_is_a(prop_type, gtk.Adjustment):
                value = gtk.Adjustment(0, 0, 100, 1, 10, 10)
                (value.value, value.lower, value.upper,
                 value.step_increment, value.page_increment,
                 value.page_size) = list(map(float, string.split(' ')))
            elif gobject.type_is_a(prop_type, gdk.Pixbuf):
                filename = self._build.find_resource(string)
                value = None
                if filename:
                    # XXX: Handle GError exceptions.
                    value = gdk.pixbuf_new_from_file(filename);
            elif (gobject.type_is_a(gobject.GObject, prop_type) or
                  gobject.type_is_a(prop_type, gobject.GObject)):
                value = self._build.get_widget(string)
                if value is None:
                    self._build.add_delayed_property(obj_id, pspec, string)
            else:
                value = None
        else:
            raise AssertionError("type %r is unknown" % prop_type)

        return value

    def add(self, parent, child, properties, type):
        raise NotImplementedError

    def find_internal_child(self, gobj, name):
        if name in self.child_names:
            return getattr(gobj, name)

    def get_internal_child_name(self, gobj, child):
        for child_name in self.child_names:
            if getattr(gobj, child_name) == child:
                return child_name

class UIManagerAdapter(GObjectAdapter):
    object_type = gtk.UIManager
    def add(self, parent, child, properties, type):
        parent.insert_action_group(child, 0)

class WidgetAdapter(GObjectAdapter):
    object_type = gtk.Widget
    def construct(self, name, gtype, properties):
        widget = GObjectAdapter.construct(self, name, gtype, properties)
        widget.set_name(name)
        return widget

    def prop_set_has_default(self, widget, value):
        value = str2bool(value)
        if value:
            self._build._default_widget = widget

    def prop_set_tooltip(self, widget, value):
        if isinstance(widget, gtk.ToolItem):
            # XXX: factor to separate Adapter
            widget.set_tooltip(self._build._tooltips, value, None)
        else:
            self._build._tooltips.set_tip(widget, value, None)

    def prop_set_visible(self, widget, value):
        value = str2bool(value)
        setattr(widget,'gazpacho::visible', value)
        widget.set_property('visible', value)

    def prop_set_has_focus(self, widget, value):
        value = str2bool(value)
        if value:
            self._build._focus_widget = widget
        #widget.set_data('gazpacho::has-focus', value)

    def prop_set_is_focus(self, widget, value):
        value = str2bool(value)
        #widget.set_data('gazpacho::is-focus', value)

    def prop_set_sizegroup(self, widget, value):
        widget.set_data('gazpacho::sizegroup', value)

    def prop_set_response_id(self, widget, value):
        widget.set_data('gazpacho::response-id', int(value))

class PythonWidgetAdapter(WidgetAdapter):
    def construct(self, name, gtype, properties):
        obj = self.object_type()
        obj.set_name(name)
        return obj

class ContainerAdapter(WidgetAdapter):
    object_type = gtk.Container
    def add(self, container, child, properties, type):
        if not self._add_to_dialog(container, child):
            container.add(child)

        self._set_child_properties(container, child, properties)

    def _add_to_dialog(self, parent, widget):
        if hasattr(widget, 'responseid'):
            dialog = None
            while parent:
                if isinstance(parent, gtk.Dialog):
                    dialog = parent
                    break
                parent = parent.parent

            if dialog:
                # FIXME: Limit to action_area
                dialog.add_action_widget(widget, response_id)

                # Reset, the real properties will be set afterwards
                widget.parent.set_child_packing(widget, True, True, 0,
                                                gtk.PACK_START)
                return True
        return False

    def _set_child_properties(self, container, child, properties):
        properties = self._getproperties(type(container),
                                         child.get_name(),
                                         properties,
                                         child=True)

        for name, value in properties:
            #print '%s.%s = %r (of %s)' % (child.get_name(), name, value,
            #                              gobj.get_name())
            container.child_set_property(child, name, value)

class ActionGroupAdapter(GObjectAdapter):
    object_type = gtk.ActionGroup
    def construct(self, name, gtype, properties):
        if not 'name' in properties:
            properties['name'] = name
        return GObjectAdapter.construct(self, name, gtype, properties)

    def add(self, parent, child, properties, type):
        accel_key = getattr(child, 'accel_key', None)
        if accel_key:
            accel_path = "<Actions>/%s/%s" % (parent.get_property('name'),
                                              child.get_name())
            accel_mod = getattr(child, 'accel_mod')
            gtk.AccelMap.add_entry(accel_path, accel_key, accel_mod)
            child.set_accel_path(accel_path)
            child.set_accel_group(self._build.ensure_accel())
        parent.add_action(child)

class ActionAdapter(GObjectAdapter):
    object_type = gtk.Action
    def construct(self, name, gtype, properties):
        # Gazpacho doesn't save the name for actions
        # So we have set it manually.
        if not 'name' in properties:
            properties['name'] = name
        return GObjectAdapter.construct(self, name, gtype, properties)

    def _set_accel(self, action, accel_key, accel_mod):
        if not accel_key:
            return

        setattr(action, 'accel_key', accel_key)
        setattr(action, 'accel_mod', accel_mod)

    def prop_set_accelerator(self, action, value):
        if not value:
            return
        self._set_accel(action, *gtk.accelerator_parse(value))

    def prop_set_stock_id(self, action, value):
        action.set_property('stock-id', value)

        # Set the accelerator from the stock item, but only if it's
        # not set already

        if action.get_accel_path():
            return

        # FIXME: Should we print a warning if it cannot be found
        #stock_item = gtk.stock_lookup(value)
        #if stock_item:
        #    self._set_accel(action, stock_item[3], stock_item[2])

    # This is for backwards compatibility
    def prop_set_callback(self, action, value):
        if value:
            self._build.add_signal(action, 'activate', value)

class PixmapAdapter(WidgetAdapter):
    object_type = gtk.Image
    def prop_set_build_insensitive(self, pixmap, value):
        pixmap.set_build_insensitive(str2bool(value))

    def prop_set_filename(self, pixmap, value):
        filename = self._build.find_resource(value);
        if not filename:
            print('No such a file or directory: %s' % value)
            return

        try:
            pb = gdk.pixbuf_new_from_file(filename)
        except gobject.GError as e:
            print('Error loading pixmap: %s' % e.message)
            return
        except TypeError as e:
            print('Error loading pixmap: %s' % e)
            return

        pix, bit = pb.render_pixmap_and_mask(127)
        pixmap.set(pix, bit)

class ProgressAdapter(WidgetAdapter):
    object_type = gtk.ProgressBar
    def prop_set_format(self, progress, value):
        progress.set_format_string(value)

class ButtonAdapter(ContainerAdapter):
    object_type = gtk.Button

class OptionMenuAdapter(ButtonAdapter):
    object_type = gtk.MenuBar
    def add(self, parent, child, properties, type):
        if not isinstance(child, gtk.Menu):
            print(("warning: the child of the option menu '%s' was "
                   "not a GtkMenu"  % (child.get_name())))
            return

        parent.set_menu(child)
        self._set_child_properties(parent, child, properties)

    def prop_set_history(self, optionmenu, value):
        optionmenu.set_history(int(value))

class EntryAdapter(WidgetAdapter):
    object_type = gtk.Entry
    def prop_set_invisible_char(self, entry, value):
        entry.set_invisible_char(value.decode()[0])

class TextViewAdapter(ButtonAdapter):
    object_type = gtk.TextView
    def prop_set_text(self, textview, value):
        buffer = gtk.TextBuffer()
        buffer.set_text(value)
        textview.set_buffer(buffer)

class CalendarAdapter(WidgetAdapter):
    object_type = gtk.Calendar
    def prop_set_display_options(self, calendar, value):
        options = flagsfromstring(value, flags=gtk.CalendarDisplayOptions)
        calendar.display_options(options)

class WindowAdapter(ContainerAdapter):
    object_type = gtk.Window
    def prop_set_wmclass_class(self, window, value):
        window.set_wmclass(value, window.wmclass_class)

    def prop_set_wmclass_name(self, window, value):
        window.set_wmclass(value, window.wmclass_name)

    def prop_set_type_hint(self, window, value):
        setattr(window, 'typehint',
                        enumfromstring(value, enum=gdk.WindowTypeHint))

class NotebookAdapter(ContainerAdapter):
    object_type = gtk.Notebook
    def add(self, notebook, child, properties, type):
        tab_item = False
        for propinfo in properties[:]:
            if (propinfo.name == 'type' and
                propinfo.data == 'tab'):
                tab_item = True
                properties.remove(propinfo)
                break

        if tab_item:
            children = notebook.get_children()
            body = notebook.get_nth_page(len(children) - 1)
            notebook.set_tab_label(body, child)
        else:
            notebook.append_page(child)

        self._set_child_properties(notebook, child, properties)

class ExpanderAdapter(ContainerAdapter):
    object_type = gtk.Expander, gtk.Frame
    def _get_label_item(self, properties):
        for propinfo in properties[:]:
            if (propinfo.name == 'type' and
                propinfo.data == 'label_item'):
                properties.remove(propinfo)
                return True
        return False

    def add(self, expander, child, properties, type):
        if self._build._version == 'libglade':
            label_item = self._get_label_item(properties)
        elif type == 'label_item':
            label_item = True
        else:
            label_item = False

        if label_item:
            expander.set_label_widget(child)
        else:
            expander.add(child)

        self._set_child_properties(expander, child, properties)

class MenuItemAdapter(ContainerAdapter):
    object_type = gtk.MenuItem
    def add(self, menuitem, child, properties, type):
        if isinstance(child, gtk.Menu):
            menuitem.set_submenu(child)
        else:
            print('FIXME: Adding a %s to a %s' % (gobject.type_name(child),
                        gobject.type_name(self.object_type)))
            # GtkWarning: Attempting to add a widget with type GtkImage to a
            # GtkImageMenuItem, but as a GtkBin subclass a GtkImageMenuItem
            # can only contain one widget at a time; it already contains a
            # widget of type GtkAccelLabel'
            #menuitem.add(child)

        self._set_child_properties(menuitem, child, properties)

    def prop_set_label(self, menuitem, value):
        child = menuitem.child

        if not child:
            child = gtk.AccelLabel("")
            child.set_alignment(0.0, 0.5)
            menuitem.add(child)
            child.set_accel_widget(menuitem)
            child.show()

        if isinstance(child, gtk.Label):
            child.set_text(value)

    def prop_set_use_underline(self, menuitem, value):
        child = menuitem.child

        if not child:
            child = gtk.AccelLabel("")
            child.set_alignment(0.0, 0.5)
            menuitem.add(child)
            child.set_accel_widget(menuitem)
            child.show()

        if isinstance(child, gtk.Label):
            child.set_use_underline(str2bool(value))

    def prop_set_use_stock(self, menuitem, value):
        child = menuitem.child

        if not child:
            child = gtk.AccelLabel("")
            child.set_alignment(0.0, 0.5)
            menuitem.add(child)
            child.set_accel_widget(menuitem)
            child.show()

        value = str2bool(value)
        if not isinstance(child, gtk.Label) or not value:
            return

        stock_id = child.get_label()

        retval = gtk.stock_lookup(stock_id)
        if retval:
            _, label, modifier, keyval, _ = retval
            # put in the stock image next to the text.  Done before
            # messing with the label child, so that stock_id doesn't
            # become invalid.
            if isinstance(menuitem, gtk.ImageMenuItem):
                image = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_MENU)
                menuitem.set_image(image)
                image.show()

            child.set_text(label)
            child.set_use_underline(True)

            if keyval:
                # This triggers a segfault on exit (pachi.glade), weird
                menuitem.add_accelerator('activate',
                                         self._build.ensure_accel(),
                                         keyval, modifier,
                                         gtk.ACCEL_VISIBLE)
        else:
            print("warning: could not look up stock id '%s'" % stock_id)

class CheckMenuItemAdapter(MenuItemAdapter):
    object_type = gtk.CheckMenuItem
    def prop_set_always_show_toggle(self, check, value):
        check.set_show_toggle(value)

class RadioMenuItemAdapter(MenuItemAdapter):
    object_type = gtk.RadioMenuItem
    def prop_set_group(self, radio, value):
        group = self._build.get_widget(value)
        if not group:
            print("warning: Radio button group %s could not be found" % value)
            return

        if group == radio:
            print("Group is self, skipping.")
            return

        radio.set_group(group.get_group()[0])

class ImageMenuItemAdapter(MenuItemAdapter):
    object_type = gtk.ImageMenuItem
    def find_internal_child(self, menuitem, childname):
        if childname == 'image':
            pl = menuitem.get_image()
            if not pl:
                pl = gtk.Image()
                menuitem.set_image(pl)
            return pl
        return MenuItemAdapter.find_internal_child(self, menuitem, childname)

    def get_internal_child_name(self, parent, child):
        if parent.get_image() == child:
            return 'image'
        return MenuItemAdapter.get_internal_child_name(self, parent, child)

class ToolbarAdapter(ContainerAdapter):
    object_type = gtk.Toolbar
    def prop_set_tooltips(self, toolbar, value):
        toolbar.set_tooltips(str2bool(value))

class StatusbarAdapter(ContainerAdapter):
    object_type = gtk.Statusbar
    def prop_set_has_resize_grip(self, status, value):
        status.set_has_resize_grip(str2bool(value))

#class RulerAdapter(WidgetAdapter):
#    object_type = gtk.Ruler
#    def prop_set_metric(self, ruler, value):
#        ruler.set_metric(enumfromstring(value,
#                                        enum=gtk.MetricType))

class ToolButtonAdapter(ContainerAdapter):
    object_type = gtk.ToolButton
    def prop_set_icon(self, toolbutton, value):
        filename = self._build.find_resource(value)
        if not filename:
            print('No such a file or directory: %s' % value)
            return

        pb = gdk.pixbuf_new_from_file(filename)
        if not pb:
            print("warning: Couldn't find image file: %s" %  value)
            return
        image = gtk.Image()
        image.set_from_pixbuf(pb)
        image.show()
        toolbutton.set_icon_widget(image)

class ToggleToolButtonAdapter(ToolButtonAdapter):
    object_type = gtk.ToggleToolButton
    def prop_set_active(self, toolbutton, value):
        toolbutton.set_active(str2bool(value))

def combobox_set_content_from_string(combobox, value):
    # If the "items" property is set, we create a simple model with just
    # one column of text.
    store = gtk.ListStore(str)
    combobox.set_model(store)

    # GtkComboBoxEntry creates the cell renderer itself, but we have to set
    # the column containing the text.
    if isinstance(combobox, gtk.ComboBoxEntry):
        if combobox.get_text_column() == -1:
            combobox.set_text_column(0)
    else:
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.set_attributes(cell, text=0)

    for part in value.split('\n'):
        store.append([part])

        active = combobox.get_data('gazpacho::active')
        if active:
            combobox.set_active(active)

class ComboBoxAdapter(ContainerAdapter):
    # FIXME: Internal child: entry -> get_child()
    object_type = gtk.ComboBox, gtk.ComboBoxEntry
    def prop_set_items(self, combobox, value):
        combobox_set_content_from_string(combobox, value)

    def prop_set_active(self, combobox, value):
        combobox.set_data('gazpacho::active', int(value))

        # We don't need to set the actual property here, it's done in
        # prop_set_items.

# FIXME: PyGTK does not expose vscrollbar and hscrollbar.
#
#class ScrolledWindowAdapter(WindowAdapter):
#    child_names = ['vscrollbar', 'hscrollbar']
#    object_type = gtk.ScrolledWindow
#    def get_internal_child_name(self, parent, child):
#        if parent.vscrollbar == child:
#            return 'vscrollbar'
#        elif parent.hscrollbar == child:
#            return 'hscrollbar'
#        return WindowAdapter.get_internal_child_name(self, parent, child)

class DialogAdapter(WindowAdapter):
    child_names = ['vbox', 'action_area']
    object_type = gtk.Dialog
    def get_internal_child_name(self, parent, child):
        if parent.vbox == child:
            return 'vbox'
        elif parent.action_area == child:
            return 'action_area'
        return WindowAdapter.get_internal_child_name(self, parent, child)

class ColorSelectionDialogAdapter(DialogAdapter):
    child_names = DialogAdapter.child_names + ['ok_button',
                                               'cancel_button',
                                               'help_button',
                                               'colorsel']
    object_type = gtk.ColorSelectionDialog
    def find_internal_child(self, gobj, name):
        if name == 'color_selection':
            return gobj.colorsel

        return DialogAdapter.find_internal_child(self, gobj, name)

    def get_internal_child_name(self, parent, child):
        if parent.colorsel == child:
            return 'color_selection'
        return DialogAdapter.get_internal_child_name(self, parent, child)

class FontSelectionDialogAdapter(DialogAdapter):
    object_type = gtk.FontSelectionDialog
    child_names = DialogAdapter.child_names + ['ok_button',
                                               'cancel_button',
                                               'apply_button',
                                               'fontsel']
    def find_internal_child(self, gobj, name):
        if name == 'font_selection':
            return gobj.fontsel

        return DialogAdapter.find_internal_child(self, gobj, name)

    def get_internal_child_name(self, parent, child):
        if parent.fontsel == child:
            return 'font_selection'
        return DialogAdapter.get_internal_child_name(self, parent, child)

class TreeViewAdapter(ContainerAdapter):
    object_type = gtk.TreeView
    def add(self, treeview, child, properties, type):
        if not isinstance(child, gtk.TreeViewColumn):
            raise TypeError("Children of GtkTreeView must be a "
                            "GtkTreeViewColumns, not %r" % child)

        treeview.append_column(child)

        # Don't chain to Container add since children are not widgets

class CellLayoutAdapter(GObjectAdapter):
    def set_cell_renderer_attributes(self, gobj, cell_renderer, attributes):
        raise NotImplementedError

class TreeViewColumnAdapter(CellLayoutAdapter):
    object_type = gtk.TreeViewColumn

    def construct(self, name, gtype, properties):
        gobj = super(TreeViewColumnAdapter, self).construct(name, gtype,
                                                            properties)
        gobj.name = name
        return gobj

    def add(self, column, child, properties, type):
        if not isinstance(child, gtk.CellRenderer):
            raise TypeError("Children of GtkTreeViewColumn must be a "
                            "GtkCellRenderers, not %r" % child)

        expand = True
        pack_start = True
        for propinfo in properties[:]:
            name = propinfo.name
            if name == 'expand':
                expand = str2bool(propinfo.data)
                properties.remove(propinfo)
            elif name == 'pack_start':
                pack_start = str2bool(propinfo.data)
                properties.remove(propinfo)
            else:
                raise AssertionError("Unknown property for "
                                     "GtkTreeViewColumn: %s" % name)
        if pack_start:
            column.pack_start(child, expand)
        else:
            column.pack_end(child, expand)

    def set_cell_renderer_attributes(self, column, cell_renderer, attributes):
        for name, value in list(attributes.items()):
            column.add_attribute(cell_renderer, name, value)

        # this is ugly but's the only way to retrieve the attributes later on
        cell_renderer.set_data('gazpacho::attributes', attributes)

# Gross hack to make it possible to use FileChooserDialog on win32.
# See bug http://bugzilla.gnome.org/show_bug.cgi?id=314527
class FileChooserDialogHack(gtk.FileChooserDialog):
    def get_children(self):
        return []

class FileChooserDialogAdapter(DialogAdapter):
    gobject.type_register(FileChooserDialogHack)

class ImageAdapter(WidgetAdapter):
    object_type = gtk.Image
    def prop_set_file(self, image, value):
        newvalue = self._build.find_resource(value)
        if newvalue:
            image.set_property('file', newvalue)
        image.set_data('image-file-name', value)

class ListStoreAdapter(GObjectAdapter):
    object_type = gtk.ListStore

    def construct(self, name, gtype, properties):
        gobj = super(ListStoreAdapter, self).construct(name, gtype,
                                                       properties)
        gobj.name = name
        return gobj

    def set_column_types(self, store, columns):
        if columns:
            types = [col.type for col in columns]
            store.set_column_types(*types)

    def fill(self, store, rows):
        types = [store.get_column_type(i) for i in range(store.get_n_columns())]
        for row_info in rows:
            values = []
            for col_info in row_info.cols:
                gtype = types[col_info.id]
                value = valuefromstringsimpletypes(gtype, col_info.data)
                values.append(value)

            store.append(values)

# Global registry
adapter_registry = AdapterRegistry()
