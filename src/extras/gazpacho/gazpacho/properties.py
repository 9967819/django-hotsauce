# Copyright (C) 2005-2006 by Johan Dahlin
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

# properties.py - More black magic than Dumbledore can handle

import sys

import gobject
import gtk
from kiwi.environ import environ
from kiwi.component import implements

from gazpacho.choice import enum_to_string, flags_to_string
from gazpacho.interfaces import IReferencable
from gazpacho.command import Command
from gazpacho.i18n import _

UNICHAR_PROPERTIES = ('invisible-char', )

class PropertyError(Exception):
    pass

class UnsupportedProperty(PropertyError):
    pass

class PropertySetError(PropertyError):
    """
    This can only be raised inside a set handler of a PropType subclass.
    It is raised when an invalid value set, for example when the position
    of a cell in a table is outside of the table borders.
    """

class PropertyCustomEditor(object):
    """
    Base class for editors for custom properties

    The create method is called the first time a widget with this property is
    shown in the editor. Then, every time an instance of this type of widget is
    selected the 'update' method is called with the proper information to
    manipulate the widget.

    Because of that this should not store any information about the state of
    the widget that is being edited.
    """

    # if wide_editor is True the editor will expand both columns of the
    # editor page
    wide_editor = False

    def get_editor_widget(self):
        "Return the gtk widget that implements this editor"

    def update(self, context, widget, proxy):
        """
        Called when a widget with this property is selected

        @param    context: gazpacho context to get the current app and project
        @param widget: the widget we are editing
        @param      proxy: an object that should be used to update the widget.
                           This is what allows the undo/redo mechanism actually
                           works
        """

class PropStorage:
    """A PropStorage is a bag where we keep PropTypes

    It is used in PropRegistry to store the regular properties and the child
    properties.
    """
    child = False
    def __init__(self):
        self._types = {}
        self._custom = {}
        self._pspec_cache = {}

    def _add_type(self, prop_name, prop_type, pspec=None):
        if pspec:
            if gobject.type_is_a(pspec.value_type, gobject.TYPE_ENUM):
                prop_type.enum_class = pspec.enum_class
            elif gobject.type_is_a(pspec.value_type, gobject.TYPE_FLAGS):
                prop_type.flags_class = pspec.flags_class

            prop_type.label = pspec.nick
            prop_type.type = pspec.value_type
        else:
            if not prop_type.label:
                prop_type.label = prop_name.capitalize()

        if prop_name in self._types:
            msg = "There is already a property called %s registered"
            raise TypeError(msg % prop_name)

        self._types[prop_name] = prop_type

    def list(self, type_name, prop_registry):
        """
        List all the properties for type_name
        If parent is specified, child properties will also be included.
        This method will create the prop_types and save if they're
        not already created.

        @param type_name: name of type
        @type  type_name: string
        @param prop_registry: property registry
        @type  prop_registry: a PropRegistry
        """
        property_types = []
        for pspec in self._list_properties(type_name):
            prop = self._get_type_from_prop_name(type_name, pspec.name)
            if not prop:
                base = prop_registry._get_base_type(pspec.value_type)
                prop = self.create_type_from_pspec(pspec, base, type_name)
            property_types.append(prop)

        property_types.extend(self._list_custom(type_name))

        for prop_type in property_types[:]:
            if (not prop_type.readable or
                not prop_type.writable or
                not prop_type.enabled):
                property_types.remove(prop_type)

        return property_types

    def has_prop_type(self, type_name, prop_name):
        """
        True if a property from type_name called prop_name exists

        @param type_name: gtype name of owner
        @type  type_name: string
        @param prop_name: name of property
        @type  prop_name: string
        """
        prop_type = self._get_type_from_prop_name(type_name, prop_name)
        if not prop_type:
            prop_type = self._get_custom(type_name, prop_name)

        return prop_type

    def get_prop_type(self, type_name, prop_name, prop_registry):
        """
        Fetch a property from type_name called prop_name, it creates
        the property type if it's not already created.

        @param type_name: gtype name of owner
        @type  type_name: string
        @param prop_name: name of property
        @type  prop_name: string
        @param prop_registry: property registry
        @type  prop_registry: a PropRegistry
        """
        prop_type = self._get_type_from_prop_name(type_name, prop_name)
        if not prop_type:
            prop_type = self._get_custom(type_name, prop_name)

        if not prop_type:
            pspec = self.get_pspec(type_name, prop_name)
            if pspec:
                base = prop_registry._get_base_type(pspec.value_type)
                prop_type = self.create_type_from_pspec(pspec, base, type_name)

        return prop_type

    def add_custom_type(self, klass, type_name, prop_name, pspec):
        custom = self._custom.setdefault(type_name, [])
        if prop_name in custom:
            return
        klass.custom = True
        custom.append(prop_name)
        self._add_type(type_name + '::' + prop_name, klass, pspec)

    def _get_custom(self, type_name, prop_name):
        """
        Get custom properties from type_name, called prop_name
        """
        for prop_type in self._list_custom(type_name):
            if prop_type.name == prop_name:
                return prop_type

    def _list_custom(self, type_name):
        """
        List custom properties for type_name, check the type and
        all the parent types
        """
        retval = []
        while True:
            for prop_name in self._custom.get(type_name, []):
                full_name = type_name + '::' + prop_name
                retval.append(self._types[full_name])

            if type_name == 'GObject':
                break

            type_name = gobject.type_name(gobject.type_parent(type_name))

        return retval

    def get_pspec(self, type_name, prop_name):
        for pspec in self._list_properties(type_name):
            if pspec.name == prop_name:
                return pspec

    def has_property(self, type_name, prop_name):
        "Checks if  type_name has a property with name prop_name"
        return self.get_pspec(type_name, prop_name) != None

    def _list_properties(self, type_name):
        "List all properties for type_name, and use a simple cache"
        pspecs = self._pspec_cache.get(type_name, [])
        if pspecs:
            return pspecs

        try:
            if self.child:
                pspecs = gtk.container_class_list_child_properties(type_name)
            else:
                pspecs = gobject.list_properties(type_name)
        except TypeError:
            raise PropertyError("Unknown GType name: %s" % type_name)
        pspecs = list(pspecs)

        self._pspec_cache[type_name] = pspecs

        return pspecs

    def _get_type_from_prop_name(self, type_name, prop_name):
        """Get the type for type_name::prop_name. If we don't have a PropType
        for this type_name, check in its parent types"""
        assert type(type_name) == str

        while True:
            full_name = type_name + '::' + prop_name
            if full_name in list(self._types.keys()):
                return self._types[full_name]

            if type_name == 'GObject':
                break

            type_name = gobject.type_name(gobject.type_parent(type_name))

    def create_type_from_pspec(self, pspec, base, type_name=None):
        if not type_name:
            type_name = gobject.type_name(pspec.owner_type)

        readable = pspec.flags & gobject.PARAM_READABLE != 0
        writable = pspec.flags & gobject.PARAM_WRITABLE != 0
        prop_type = PropMeta.new(type_name,
                                 pspec.name,
                                 pspec.blurb,
                                 base,
                                 pspec.value_type,
                                 pspec.owner_type,
                                 readable=readable,
                                 writable=writable,
                                 child=self.child,
                                 label=pspec.nick)
        self._set_interval_from_pspec(prop_type, pspec)
        self._add_type(prop_type.__name__, prop_type, pspec)
        return prop_type

    def _set_interval_from_pspec(self, prop_type, pspec):
        if not hasattr(pspec, 'maximum'):
            return

        maximum = pspec.maximum
        if maximum == -1 and pspec.value_type == gobject.TYPE_UINT:
            maximum = sys.maxsize
        prop_type.maximum = maximum

        prop_type.minimum = pspec.minimum
        prop_type.defautl = pspec.default_value

class ChildPropStorage(PropStorage):
    child = True

class PropRegistry:
    def __init__(self):
        self._bases = {}

        self._normal_storage = PropStorage()
        self._child_storage = ChildPropStorage()

    def add_base_type(self, klass, gtype):
        if not issubclass(klass, PropType):
            raise TypeError("klass needs to be a subclass of PropType")

        if gtype in self._bases:
            raise PropertyError("base type %r is already defined" % gtype)
        elif klass.base_type != None:
            raise PropertyError("klass type %r is already registered to %r" %
                                (klass, klass.base_type))

        self._bases[gtype] = klass
        klass.base_type = gtype

    def override_property(self, full_name, klass):
        """
        Create a property for full_name, (type::prop_name)
        If the property exists, please use override_simple
        @param klass: property class
        @type  klass: subclass of PropType
        @param full_name: complete name of property
        @type  full_name: string (typename::prop_name)
        """
        self._override_property_internal(self._normal_storage,
                                         full_name, klass)

    def override_child_property(self, full_name, klass):
        """
        Create a child property for full_name, (type::prop_name)
        If the property exists, please use override_simple_child
        @param klass: property class
        @type  klass: subclass of PropType
        @param full_name: complete name of property
        @type  full_name: string (typename::prop_name)
        """
        self._override_property_internal(self._child_storage, full_name, klass)
        klass.child = True

    def _override_property_internal(self, storage, full_name, klass):
        if not issubclass(klass, PropType):
            raise TypeError("klass needs to be a subclass of PropType")

        type_name, prop_name = full_name.split('::')
        pspec = storage.get_pspec(type_name, prop_name)

        # If we can't find the property in the GType, it's a custom type
        if not storage.has_property(type_name, prop_name):
            storage.add_custom_type(klass, type_name, prop_name, pspec)
        else:
            raise TypeError("%s exists, use override_simple" % full_name)

        # Note, that at this point we need to setup the overriden class
        # since we're not going to call the type constructor, so
        # this needs to be in sync with PropMeta.new

        klass.name = prop_name
        klass.owner_name = type_name
        klass.owner_type = gobject.type_from_name(type_name)

        if not issubclass(klass.custom_editor, PropertyCustomEditor):
            raise TypeError(
                "custom_editor %r for property class %r needs to be a "
                "subclass of PropertyCustomEditor " %
                (klass.custom_editor, klass))

    def override_simple(self, full_name, base=None, **kwargs):
        """
        Same as override_property, but creates and registeres the class
        @param full_name: complete name of property
        @param base:      base class
        @param child:     child property
        @param kwargs namespace to use in class
        """
        self._override_simple_internal(self._normal_storage,
                                       full_name, base, **kwargs)

    def override_simple_child(self, full_name, base=None, **kwargs):
        """
        Same as override_child_property, but creates and registeres the class
        @param full_name: complete name of property
        @param base:      base class
        @param child:     child property
        @param kwargs namespace to use in class
        """
        self._override_simple_internal(self._child_storage,
                                       full_name, base, **kwargs)

    def _override_simple_internal(self, storage, full_name, base=None,
                                  **kwargs):
        type_name, prop_name = full_name.split('::')

        pspec = storage.get_pspec(type_name, prop_name)
        if not pspec:
            raise TypeError("You can only override existing properties, %s "
                            "is not a property" % full_name)

        # check if the type already exist
        if storage.has_prop_type(type_name, prop_name):
            prop_type = storage.get_prop_type(type_name, prop_name, self)
            # If a base is provided we don't modify the original proptype
            # but create a new one. This ensures the parent prop is not changed
            if base and prop_type == base:
                klass = type(full_name, (base,), kwargs)

                prop_type = storage.create_type_from_pspec(pspec,
                                                           klass,
                                                           type_name=type_name)
            else:
                # simply update the prop_type
                for key, value in list(kwargs.items()):
                    setattr(prop_type, key, value)

        else:
            if not base:
                base = self._get_base_type(pspec.value_type)

            klass = type(full_name, (base,), kwargs)

            prop_type = storage.create_type_from_pspec(pspec,
                                                       klass,
                                                       type_name=type_name)

        return prop_type

    def list(self, type_name, parent=None):
        """
        List all the properties for type_name
        If parent is specified, child properties will also be included.
        This method will create the prop_types if they're not already created.

        @param type_name: name of type
        @type  type_name: string
        @param parent:    parent type of object
        @type  parent:    GType
        """
        property_types = self._normal_storage.list(type_name, self)

        if parent:
            parent_type = gobject.type_name(parent)
            property_types.extend(self._child_storage.list(parent_type, self))

        return property_types

    def get_prop_type(self, type_name, prop_name, parent=None):
        """
        Fetch a property from type_name called prop_name. It creates
        the property type if it's not already created.

        @param type_name: gtype name of owner
        @type  type_name: string
        @param prop_name: name of property
        @type  prop_name: string
        """
        if parent:
            parent_type = gobject.type_name(parent)
            prop_type = self._child_storage.get_prop_type(parent_type,
                                                          prop_name, self)

        else:
            prop_type = self._normal_storage.get_prop_type(type_name,
                                                           prop_name, self)

        return prop_type

    def _get_base_type(self, value_type):
        if gobject.type_is_a(value_type, gobject.TYPE_OBJECT):
            base_type = gobject.TYPE_OBJECT
        elif gobject.type_is_a(value_type, gobject.TYPE_ENUM):
            base_type = gobject.TYPE_ENUM
        elif gobject.type_is_a(value_type, gobject.TYPE_FLAGS):
            base_type = gobject.TYPE_FLAGS
        elif gobject.type_is_a(value_type, gobject.TYPE_BOXED):
            base_type = gobject.TYPE_BOXED
        else:
            base_type = value_type

        base = self._bases.get(base_type)
        if not base:
            raise PropertyError("Can't find base type for %r" % base_type)
        return base


    def get_writable_properties(self, widget, child):
        """
        Lists all the writable properties, eg, the ones we'd like
        to have saved in a persistent format, eg glade files

        @param widget: a gtk.Widget
        @param child: True to list child properties, False to omit them
        """
        if child:
            parent_type = gobject.type_name(widget.get_parent())
            property_types = self._child_storage.list(parent_type, self)

        else:
            type_name = gobject.type_name(widget)
            property_types = self._normal_storage.list(type_name, self)

        properties = []
        # write the properties
        for prop_type in property_types:
            # don't save the name property since it is saved in the id
            # attribute of the tag
            if prop_type.name == 'name':
                continue

            # Do not save non-editable gobject properties, eg
            # GtkWindow::screen
            # hack?
            if (prop_type.base_type == gobject.GObject.__gtype__ and
                not prop_type.editable):
                continue

            if not prop_type.persistent:
                continue

            properties.append(prop_type)

        return properties

class PropMeta(type):
    """
    I am a metaclass used for Property types.
    Currently I only offer a __repr__ method, but there
    is also a class method called new which is used as
    a factory for types which has me as a metaclass.
    """

    #@classmethod
    def new(mcs, owner_name, name, description, base, value_type, owner_type,
            readable=True, writable=True, child=False, label=None):

        cls = mcs(owner_name + '::' + name, (base,), {})

        # This can not be overridden
        cls.name =  name
        cls.description = description
        cls.type = value_type
        cls.owner_name = owner_name
        cls.owner_type = owner_type

        # Be very careful here.
        # Do not overwrite anything, since we want this class
        # to be as transparent as possible.
        # Eg when doing:
        #
        # class Overridden(Custom, Int):
        #   ...
        # pr.override('some-prop', Foo)
        #
        # We want to have methods and attributes in the overridden to
        # to take precedence over the one in the transparent subclass
        # we're going to create, so check before assigning anything.

        if cls.readable is None:
            cls.readable = readable

        if cls.writable is None:
            cls.writable = writable

        if not cls.readable:
            getter = PropType._value_not_readable
        elif child:
            getter = base._child_get
        else:
            getter = base._get

        if not cls.writable:
            setter = PropType._value_not_writable
        elif child:
            setter = base._child_set
        else:
            setter = base._set

        if cls.value is None:
            cls.value = property(getter, setter)
        if not cls.set:
            cls.set = setter
        if not cls.get:
            cls.get = getter
        cls.child = child

        if not cls.label:
            # XXX: tooltip
            if not label:
                label = name.capitalize()
            cls.label = label

        return cls
    new = classmethod(new)

    def __repr__(mcs):
        child = ''
        if mcs.child:
            child = ' (child)'
        return '<PropType %s%s>' % (mcs.__name__, child)

class PropType(object, metaclass=PropMeta):
    """
    I am the base class for all properties.
    I wrap a GParamSpec (or custom property types), instances
    of me wrap a GObject property.

    @cvar name:         name of the property, eg expand
    @cvar description:  description of the property (it'll show in a tooltip)
    @cvar owner_name:   owner gobject name: GtkWindow
    @cvar type:         type, GType of property
    @cvar owner_type:   type of owner
    @cvar value:        value property
    @cvar readable:     can the value be retreived
    @cvar writable:     if it's possible to change values
    @cvar set:          set method
    @cvar get:          get method
    @cvar child:
    @cvar enabled:
    @cvar translatable: marked as translatable
    @cvar label:        property descriptor for set/get
    @cvar default:
    @cvar custom:
    @cvar editable:
    @cvar base_type:
    @cvar editor:        editor
    @cvar custom_editor: specialized editor
    @cvar persistent:    Should we save the property?
    @cvar priority:      Higher priorities appear before lower priorities in
                         the property editor
    @cvar has_custom_default: the prop has been customized with a default
    """

    name = None
    description = None
    owner_name = None
    type = None
    owner_type = gobject.TYPE_INVALID
    value = None
    readable = None
    writable = None
    set = None
    get = None
    child = None
    enabled = True
    translatable = False
    label = None
    default = None
    custom = False
    editable = True
    base_type = None
    editor = None
    custom_editor = PropertyCustomEditor
    persistent = True
    priority = 100
    has_custom_default = False

    def __init__(self, gadget):
        self._initial = None

        cls = type(self)
        assert cls.name != None
        assert cls.owner_name != None
        assert cls.owner_type != gobject.TYPE_INVALID

        self.gadget = gadget
        self._project = gadget.project
        gobj = gadget.widget

        # Assert that the owner is of correct type
        if self.child:
            test_object = gobj.get_parent()
        else:
            test_object = gobj
        if not gobject.type_is_a(test_object, self.owner_type):
            raise TypeError("Expected an object of type %s, got %r" % (
                gobject.type_name(self.owner_type), test_object))

        self.load()

    #@property
    def get_object(self):
        return self.gadget.widget
    object = property(get_object)

    def load(self):
        parent_name = None
        if self.child:
            parent_name = gobject.type_name(self.object.get_parent())

        # use the gtk value if this is an internal child
        if self.gadget.internal_name or self.gadget.maintain_gtk_properties:
            self._initial = self.gadget.adaptor.get_default_prop_value(
                self, parent_name)
            # we have to initialize _value from the gtk widget
            if self.custom:
                self._value = self._initial
            else:
                if self.child:
                    parent = self.object.get_parent()
                    self._value = parent.child_get_property(self.object,
                                                            self.name)
                else:
                    # FIXME: This is broken, but needed for
                    # GtkRadioButton::group,
                    # see tests.test_glade.GladeTest.test_radiobutton
                    try:
                        self._value = self.object.get_property(self.name)
                    except TypeError:
                        self._value = None
        else:
            if self.custom or self.has_custom_default:
                self._initial = self.default
                self.set(self.default)
            else:
                self._initial = self.gadget.adaptor.get_default_prop_value(
                    self, parent_name)

    def get_project(self):
        return self._project

    def get_object_name(self):
        if isinstance(self.object, gtk.Widget):
            return self.object.name

        return repr(self.object)

    def add_change_notify(self, function):
        if not callable(function):
            raise TypeError("function must be callable")

        if not custom:
            if self.child:
                signal_name = 'child-notify'
            else:
                signal_name = 'notify'
            self.object.connect('%s::%s' % (signal_name, self.name),
                                lambda self, obj, pspec: function(self))
    def _value_not_readable(self):
        raise PropertyError("%s not readable" % self.name)

    def _value_not_writable(self, value):
        raise PropertyError("%s not writable" % self.name)

    def _child_get(self):
        try:
            parent = self.object.get_parent()
            return parent.child_get_property(self.object, self.name)
        except TypeError as e:
            raise TypeError(
                "Failed to get child property from %r for %s "
                "(%s:%s): `%s'" % (parent, self.object,
                                   gobject.type_name(self.owner_type),
                                   self.name, e))

    def _child_set(self, value):
        try:
            parent = self.object.get_parent()
            parent.child_set_property(self.object,
                                      self.name,
                                      value)
        except TypeError as e:
            raise TypeError("Failed to set property %s:%s to %s: `%s'" % (
                gobject.type_name(self.owner_type), self.name, value, e))


    def _get(self):
        try:
            return self.object.get_property(self.name)
        except TypeError as e:
            raise TypeError("Error while getting %s:%s `%s'" % (
                gobject.type_name(self.owner_type), self.name, e))

    def _set(self, value):
        try:
            self.object.set_property(self.name, value)
        except TypeError as e:
            raise TypeError("Error while setting %s:%s to %s `%s'" % (
                gobject.type_name(self.owner_type), self.name, value, e))

    def get_default(self, gobj):
        if self.custom or self.has_custom_default:
            return self.default

        if self.child:
            parent = gobj.get_parent()
            return parent.child_get_property(gobj, self.name)

        return gobj.get_property(self.name)

    def is_translatable(self):
        """
        Is the property translatable?
        By default we're using a class variable, but in
        some cases we want to be able to check the instance
        state and check if we want translatation, eg GtkButton::label,
        in those cases, just override this method
        """
        return self.translatable

    def save(self):
        """
        Marshal the property into a string
        Return None if it already contains the default value
        """
        value = self.get()
        if not self.has_custom_default:
            if value == None or value == self._initial:
                return

        return str(value)

    def __repr__(self):
        return '<Property %s:%s value=%r>' % (self.owner_name, self.name,
                                              self.get())

# XXX: This is a really bad name since it conflicts with
#      the custom widget
class CustomProperty(PropType):
    readable = True
    writable = True
    def __init__(self, object):
        self._functions = []
        super(CustomProperty, self).__init__(object)

    def get(self):
        return self._get()

    def set(self, value):
        self._set(value)

    def add_change_notify(self, function):
        self._functions.append(function)

    def notify(self):
        for function in self._functions:
            function(self)

    value = property(lambda self: self.get(),
                     lambda self, value: self.set(value))

# This is of course a big hack, but it is for some reason
# required for epydoc to run
if environ.epydoc:
    class FakeRegistry:
        def add_base_type(self, *args, **kwargs):
            pass
        def override_property(self, *args, **kwargs):
            pass
        def override_simple(self, *args, **kwargs):
            pass
        def get_prop_type(self, *args, **kwargs):
            pass
    prop_registry = FakeRegistry()
    custom = object
else:
    prop_registry = PropRegistry()
    custom = CustomProperty

class CustomChildProperty(custom):
    child = True
    def get(self):
        return self._child_get()

    def set(self, value):
        self._child_set(value)

class TransparentProperty(custom):
    """
    A transparent property is a property which does not
    update the property of the GObject, instead it keeps track
    of the value using other means.
    For instance GtkWindow::modal is a transparent property, since
    we do not want to make the window we editing modal.
    """
    def __init__(self, *args):
        super(TransparentProperty, self).__init__(*args)
        self._value = self._initial

    def get(self):
        return self._value

    def set(self, value):
        self._value = value

class BooleanType(PropType):
    default = False
prop_registry.add_base_type(BooleanType, gobject.TYPE_BOOLEAN)

class PointerType(PropType):
    pass
prop_registry.add_base_type(PointerType, gobject.TYPE_POINTER)

class StringType(PropType):
    default = ''
    multiline = False
    translatable = True
    has_i18n_context = True
    i18n_comment = ''
prop_registry.add_base_type(StringType, gobject.TYPE_STRING)

class ObjectType(PropType):

    implements(IReferencable)

    editable = False

    def set(self, widget):
        from gazpacho.gadget import Gadget

        # remove old reference
        old_widget = self.get()
        if old_widget:
            old_gadget = Gadget.from_widget(old_widget)
            old_gadget.references.remove_referrer(self)

        # add new reference
        if widget:
            gadget = Gadget.from_widget(widget)
            gadget.references.add_referrer(self)

        #super(ObjectType, self).set(widget)
        self._set(widget)

    def save(self):
        value = self.get()
        if value:
            return value.get_name()

    # IReferencable

    def remove_reference(self, gadget):
        """
        See L{gazpacho.interfaces.IReferencable.remove_reference}
        """
        self.object.set_property(self.name, None)

    def add_reference(self, gadget):
        """
        See L{gazpacho.interfaces.IReferencable.add_reference}
        """
        self.object.set_property(self.name, gadget.widget)

prop_registry.add_base_type(ObjectType, gobject.TYPE_OBJECT)

#
# Numbers
#

class BaseNumericType(PropType):
    """
    Base type class used for all numeric types,
    The additional class variables here are used to create a
    GtkAlignment for the editors
    """
    default = 0
    # GtkAdjustment
    minimum = 0
    maximum = 0
    step_increment = 1
    page_increment = 10

    # SpinButton
    # acceleration factor
    climb_rate = 1

    # number of decimals
    digits = 0

    #@classmethod
    def get_adjustment(cls):
        #if not cls.minimum <= cls.default <= cls.maximum:
        #    raise TypeError(
        #        "default must be larger than minimum and lower "
        #        "than maximum (%r <= %r <= %r) for %s::%s (%r)" % (
        #        cls.minimum, cls.default, cls.maximum,
        #        gobject.type_name(cls.owner_type), cls.name, cls.type))

        return gtk.Adjustment(value=cls.default,
                              lower=cls.minimum,
                              upper=cls.maximum,
                              step_incr=cls.step_increment,
                              page_incr=cls.page_increment)
    get_adjustment = classmethod(get_adjustment)

class BaseFloatType(BaseNumericType):
    """
    Base float type, used by float and double
    """
    default = 0.0
    minimum = -10.0**308
    maximum = 10.0**308
    digits = 2
    def save(self):
        if not BaseNumericType.save(self):
            return
        # Fix for #326723
        # kiwi/datatypes.py uses %.12g here, but it seems to
        # be too precise, 0.1 -> 0.10000000149
        value = self.get()
        strvalue = str(value)
        if strvalue.endswith('.0'):
            return strvalue
        return '%.8g' % value

class IntType(BaseNumericType):
    minimum = -int(2**31-1)
    maximum = int(2**31-1)
prop_registry.add_base_type(IntType, gobject.TYPE_INT)

class UIntType(BaseNumericType):
    maximum = 2**32-1
prop_registry.add_base_type(UIntType,  gobject.TYPE_UINT)

class FloatType(BaseFloatType):
    pass
prop_registry.add_base_type(FloatType, gobject.TYPE_FLOAT)

class DoubleType(BaseFloatType):
    pass
prop_registry.add_base_type(DoubleType, gobject.TYPE_DOUBLE)


#
# Enum & Flags
#

class EnumType(PropType):
    enum_class = None

    #@classmethod
    def get_choices(cls):
        choices = []
        if not hasattr(cls.enum_class, '__enum_values__'):
            raise UnsupportedProperty

        for enum in list(cls.enum_class.__enum_values__.values()):
            choices.append((enum.value_nick, enum))
        choices.sort()
        return choices
    get_choices = classmethod(get_choices)

    def save(self):
        value = self.get()
        if value == self._initial:
            return

        return enum_to_string(value, enum=self.enum_class)

prop_registry.add_base_type(EnumType, gobject.TYPE_ENUM)

class FlagsType(PropType):
    flags_class = None

    #@classmethod
    def get_choices(cls):
        if not hasattr(cls.flags_class, '__flags_values__'):
            raise UnsupportedProperty

        flags = [(flag.first_value_name, mask)
                     for mask, flag in list(cls.flags_class.__flags_values__.items())
                         # we avoid composite flags
                         if len(flag.value_names) == 1]
        flags.sort()
        return flags
    get_choices = classmethod(get_choices)

    def save(self):
        value = self.get()
        if value == self._initial:
            return
        return flags_to_string(value, flags=self.flags_class)

prop_registry.add_base_type(FlagsType, gobject.TYPE_FLAGS)

class BoxedType(PropType):
    pass
prop_registry.add_base_type(BoxedType, gobject.TYPE_BOXED)

class CharType(PropType):
    default = '\0'
prop_registry.add_base_type(CharType, gobject.TYPE_CHAR)

class AdjustmentType(TransparentProperty):
    def save(self):
        adj = self.get()
        s = []
        for value in (adj.value, adj.lower, adj.upper,
                      adj.step_increment, adj.page_increment,
                      adj.page_size):
            # If it's a float which ends with .0, convert to an int,
            # so we can avoid saving unnecessary decimals
            if str(value).endswith('.0'):
                value = int(value)
            s.append(str(value))
        return ' '.join(s)
prop_registry.add_base_type(AdjustmentType, gtk.Adjustment)

class ProxiedProperty(TransparentProperty):
    target_name = None

    def get_target(self):
        raise NotImplementedError

    def get(self):
        target = self.get_target()
        return target.get_property(self.target_name)

    def set(self, value):
        target = self.get_target()
        return target.set_property(self.target_name, value)

# TODO
#   TYPE_INT64
#   TYPE_LONG
#   TYPE_UCHAR
#   TYPE_UINT64
#   TYPE_ULONG
#   TYPE_UNICHAR

# Property commands
class CommandSetProperty(Command):
    def __init__(self,  property, value):
        description = _('Setting %s of %s') % (
            property.name, property.get_object_name())
        Command.__init__(self, description)
        self._property = property
        self._value = value

    def execute(self):
        new_value = self._value
        # store the current value for undo
        self._value = self._property.value
        self._property.set(new_value)

        # TODO: this should not be needed
        # if the property is the name, we explicitily set the name of the
        # gadget to trigger the notify signal so several parts of the
        # interface get updated
        if self._property.name == 'name':
            self._property.object.notify('name')

    def unifies(self, other):
        if isinstance(other, CommandSetProperty):
            return self._property is other._property
        return False

    def collapse(self, other):
        self.description = other.description
        other.description = None

class CommandSetTranslatableProperty(CommandSetProperty):
    def __init__(self,  property, value, comment, translatable, has_context):
        CommandSetProperty.__init__(self, property, value)
        self._comment = comment
        self._translatable = translatable
        self._has_context = has_context

    def execute(self):
        new_comment = self._comment
        new_translatable = self._translatable
        new_has_context = self._has_context

        # store the current value for undo
        self._comment = self._property.i18n_comment
        self._translatable = self._property.translatable
        self._has_context = self._property.has_i18n_context

        CommandSetProperty.execute(self)

        self._property.translatable = new_translatable
        self._property.i18n_comment = new_comment
        self._property.has_i18n_context = new_has_context

if __name__ == '__main__':
    win = gtk.Window()
    box = gtk.HBox()
    win.add(box)
    button = gtk.Button()
    box.pack_start(button)

    from gazpacho.catalog import load_catalogs
    load_catalogs()

    for ptype in prop_registry.list('GtkButton', gtk.VBox):
        print(ptype, ptype.value)

    #for ptype in prop_registry.list('GtkHBox', gtk.Window):
    #    #if not ptype.child:
    #    #    continue
    #    prop = ptype(box, None)
    #    if prop.readable:
    #        print ptype, prop.value

    raise SystemExit

