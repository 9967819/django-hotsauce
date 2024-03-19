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

"""This module defines a Registry class used to store some widget data and
able to perform some queries on that, such as getting a widget's adaptor from
its name or gobject type.

This module also creates a WidgetRegistry instance variable named
widget_registry that can be imported in other modules and used as a
global registry object.
"""

import gobject

from gazpacho.interfaces import BaseWidgetAdaptor

class _Nothing:
    pass

class WidgetRegistry:
    """
    This class is used to store some widget data and able to perform
    some queries on that, such as getting a widget's adaptor from
    its name or gobject type.
    """

    def __init__(self):
        self._widget_adaptors = {}

    def add(self, widget_adaptor):
        """
        Register a widget_adaptor
        @param widget_adaptor: a BaseWidgetAdaptor subclass
        """
        if not isinstance(widget_adaptor, BaseWidgetAdaptor):
            raise TypeError("widget_adaptor must be a BaseWidgetAdaptor "
                            "instance not %r" % type(widget_adaptor))

        # If name is specified, register it two times, hack warning
        if widget_adaptor.name:
            self._widget_adaptors[widget_adaptor.name] = widget_adaptor

        name = gobject.type_name(widget_adaptor.type)
        if name in self._widget_adaptors:
            raise TypeError("%s is already registered" % name)

        self._widget_adaptors[name] = widget_adaptor

    def get_by_name(self, type_name, default=_Nothing):
        """Return widget_adaptor for type_name or None if type_name is not
        registered
        """
        if default is not _Nothing and not self.has_name(type_name):
            return
        return self._widget_adaptors.get(type_name, None)

    def get_by_name_closest(self, type_name):
        """Return widget_adaptor for type_name or closest ancestor"""
        gtype = gobject.type_from_name(type_name)
        while True:
            adapter = self._widget_adaptors.get(gobject.type_name(gtype))
            if adapter is not None:
                return adapter
            gtype = gobject.type_parent(gtype)

    def has_name(self, type_name):
        "True if type_name is registered, False otherwise"
        return type_name in self._widget_adaptors

    def get_by_type(self, obj, default=_Nothing):
        "Return widget_adaptor for a given gobject type gtype"
        if hasattr(obj, '__gtype__'):
            gtype = obj.__gtype__
        else:
            gtype = obj
        type_name = gobject.type_name(gtype)
        return self.get_by_name(type_name, default)

widget_registry = WidgetRegistry()
