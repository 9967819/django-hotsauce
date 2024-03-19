# Copyright (C) 2004,2005 by SICEm S.L. and Imendio AB
#               2006 Johan Dahlin
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

from gazpacho.command import ContainerCommand
from gazpacho.commandmanager import command_manager
from gazpacho.i18n import _
from gazpacho.placeholder import Placeholder
from gazpacho.properties import prop_registry, \
     TransparentProperty, CustomChildProperty, UIntType, \
     CommandSetProperty, PropertySetError
from gazpacho.gadget import Gadget
from gazpacho.widgets.base.base import ContainerAdaptor

class TableAdaptor(ContainerAdaptor):

    def create(self, context, interactive=True):
        """ a GtkTable starts with a default size of 1x1, and setter/getter of
        rows/columns expect the GtkTable to hold this number of placeholders,
        so we should add it. """
        table = super(TableAdaptor, self).create(context, interactive)
        table.attach(Placeholder(), 0, 1, 0, 1)
        return table

    def post_create(self, context, table, interactive=True):
        gadget = Gadget.from_widget(table)
        gadget.get_prop('n-rows').set(3)
        gadget.get_prop('n-columns').set(3)

    def fill_empty(self, context, widget):
        pass

class TableSize(TransparentProperty, UIntType):
    def _add_placeholders(self, table, value, old_size):
        n_columns = table.get_property('n-columns')
        n_rows = table.get_property('n-rows')

        if self.name == 'n-rows':
            table.resize(value, n_columns)
            for col in range(n_columns):
                for row in range(old_size, value):
                    table.attach(Placeholder(), col, col+1, row, row+1)
        else:
            table.resize(n_rows, value)
            for row in range(n_rows):
                for col in range(old_size, value):
                    table.attach(Placeholder(), col, col+1, row, row+1)

    def _remove_children(self, table, value):
        # Remove from the bottom up

        if self.name == 'n-rows':
            start_prop = 'top-attach'
            end_prop = 'bottom-attach'
        else:
            start_prop = 'left-attach'
            end_prop = 'right-attach'

        for child in table.get_children()[::-1]:
            # We need to completely remove it
            start = table.child_get_property(child, start_prop)
            if start >= value:
                table.remove(child)
                continue

            # If the widget spans beyond the new border, we should resize it to
            # fit on the new table
            end = table.child_get_property(child, end_prop)
            if end > value:
                if end_prop == 'right-attach' and value == 0:
                    continue
                table.child_set_property(child, end_prop, value)

        if self.name == 'n-rows':
            table.resize(value, self.get())
        else:
            table.resize(self.get(), value)

    def set(self, value):
        self._value = value
        if value >= 1:
            table = self.object
            old_size = table.get_property(self.name)
            if value > old_size:
                self._add_placeholders(table, value, old_size)
            elif value < old_size:
                self._remove_children(table, value)

    def load(self):
        self._initial = self.object.get_property(self.name)

    def get(self):
        return self._value

    def save(self):
        return str(self.get())

prop_registry.override_simple('GtkTable::n-rows', TableSize)
prop_registry.override_simple('GtkTable::n-columns', TableSize)

prop_registry.override_simple('GtkTable::row-spacing',
                              minimum=0, maximum=10000)
prop_registry.override_simple('GtkTable::column-spacing',
                              minimum=0, maximum=10000)

class BaseAttach(CustomChildProperty):
    """Base class for LeftAttach, RightAttach, TopAttach and BottomAttach
    adaptors"""

    editable = False

    # virtual methods that should be implemented by subclasses:
    def _is_growing(self, value):
        """Returns true if the child widget is growing"""

    def _is_shrinking(self, value):
        """Returns true if the child widget is shrinking"""

    def _cover_placeholder(self, value, left, right, top, bottom):
        """Return True if there is a placeholder in these coordinates"""

    # Private

    def _get_attach(self, table, child):
        """Returns the four attach packing properties in a tuple"""
        right = table.child_get_property(child, 'right-attach')
        left = table.child_get_property(child, 'left-attach')
        top = table.child_get_property(child, 'top-attach')
        bottom = table.child_get_property(child, 'bottom-attach')
        return (left, right, top, bottom)

    def _cell_empty(self, table, x, y):
        """Returns true if the cell at x, y is empty. Exclude child from the
        list of widgets to check"""
        empty = True
        for w in table.get_children():
            left, right, top, bottom = self._get_attach(table, w)
            if (left <= x and (x + 1) <= right and
                top <= y and (y + 1) <= bottom):
                empty = False
                break

        return empty

    # Public

    def set(self, value):
        table = self.object.get_parent()

        # are we growing?
        if self._is_growing(value):
            # check if we need to remove some placeholder
            for ph in [w for w in table.get_children() if isinstance(w, Placeholder)]:
                lph, rph, tph, bph = self._get_attach(table, ph)
                if self._cover_placeholder(table, self.object, value,
                                           lph, rph, tph, bph):
                    table.remove(ph)

            table.child_set_property(self.object, self.name, value)

        # are we shrinking? maybe we need to create placeholders
        elif self._is_shrinking(value):
            table.child_set_property(self.object, self.name, value)
            n_columns = table.get_property('n-columns')
            n_rows = table.get_property('n-rows')
            for y in range(n_rows):
                for x in range(n_columns):
                    if self._cell_empty(table, x, y):
                        table.attach(Placeholder(), x, x+1, y, y+1)

        super(BaseAttach, self).set(value)

class LeftAttach(BaseAttach, UIntType):
    label = 'Left attachment'

    def _is_growing(self, value):
        return value < self.get()

    def _is_shrinking(self, value):
        return value > self.get()

    def _cover_placeholder(self, table, child, value,
                           left, right, top, bottom):
        top_attach = table.child_get_property(child, 'top-attach')
        bottom_attach = table.child_get_property(child, 'bottom-attach')
        if value < right and self.get() > left:
            if top >= top_attach and bottom <= bottom_attach:
                return True
            return False

prop_registry.override_simple_child('GtkTable::left-attach', LeftAttach)

class RightAttach(BaseAttach, UIntType):
    label = 'Right attachment'

    def _is_growing(self, value):
        return value > self.get()

    def _is_shrinking(self, value):
        return value < self.get()

    def _cover_placeholder(self, table, child, value,
                           left, right, top, bottom):
        top_attach = table.child_get_property(child, 'top-attach')
        bottom_attach = table.child_get_property(child, 'bottom-attach')
        if value > left and self.get() < right:
            if top >= top_attach and bottom <= bottom_attach:
                return True
        return False

prop_registry.override_simple_child('GtkTable::right-attach', RightAttach)

class BottomAttach(BaseAttach, UIntType):
    label = 'Bottom attachment'

    def _is_growing(self, value):
        return value > self.get()

    def _is_shrinking(self, value):
        return value < self.get()

    def _cover_placeholder(self, table, child,
                           value, left, right, top, bottom):
        right_attach = table.child_get_property(child, 'right-attach')
        left_attach = table.child_get_property(child, 'left-attach')
        if value > top and self.get() < bottom:
            if left >= left_attach and right <= right_attach:
                return True
        return False

prop_registry.override_simple_child('GtkTable::bottom-attach', BottomAttach)

class TopAttach(BaseAttach, UIntType):
    label = 'Top attachment'

    def _is_growing(self, value):
        return value < self.get()

    def _is_shrinking(self, value):
        return value > self.get()

    def _cover_placeholder(self, table, child,
                           value, left, right, top, bottom):
        right_attach = table.child_get_property(child, 'right-attach')
        left_attach = table.child_get_property(child, 'left-attach')
        if value < bottom and self.get() > top:
            if left >= left_attach and right <= right_attach:
                return True
        return False

prop_registry.override_simple_child('GtkTable::top-attach', TopAttach)

class CommonCustom(CustomChildProperty, UIntType):
    def __init__(self, gadget):
        super(CustomChildProperty, self).__init__(gadget)
        self._update_lock = False

    def get(self):
        return self._value

    def save(self):
        return

    def _notify_update(self, gobj, pspec):
        parent = gobj.get_parent()
        self._update_lock = True
        self.set(parent.child_get_property(gobj, pspec.name))
        self._update_lock = False

    def set(self, value):
        if not self._update_lock:
            self._update_value(value)

        self._value = value
        self.notify()

class XPos(CommonCustom):
    label = 'X position'
    priority = 1

    def load(self):
        object = self.object
        parent = self.object.get_parent()
        self._value = parent.child_get_property(object, 'left-attach')
        self.object.connect('child-notify::left-attach', self._notify_update)

    def _update_value(self, value):
        gadget = self.gadget
        n_columns = gadget.get_parent().get_prop('n-columns').value
        left = gadget.get_child_prop('left-attach')
        right = gadget.get_child_prop('right-attach')
        span = right.value - left.value

        if value > n_columns - span:
            raise PropertySetError

        diff = value - self._value

        # Order is important, GtkTable does not allow us to have
        # a child which does not take up any space at all, eg
        # left-attach = right-attach
        cmd_left = CommandSetProperty(left, left.value + diff)
        cmd_right = CommandSetProperty(right, right.value + diff)
        if diff > 0:
            cmds = [cmd_right, cmd_left]
        else:
            cmds = [cmd_left, cmd_right]
        command_manager.execute(ContainerCommand(
            _('Moving widget to x position %d') % value, *cmds),
                                self.gadget.project, nested=False)

prop_registry.override_child_property('GtkTable::x-pos', XPos)

class YPos(CommonCustom):
    label = 'Y position'
    priority = 2

    def load(self):
        object = self.object
        parent = self.object.get_parent()
        self._value = parent.child_get_property(object, 'top-attach')
        self.object.connect('child-notify::top-attach', self._notify_update)

    def _update_value(self, value):
        gadget = self.gadget
        n_rows = gadget.get_parent().get_prop('n-rows').value
        top = gadget.get_child_prop('top-attach')
        bottom = gadget.get_child_prop('bottom-attach')
        span = bottom.value - top.value

        if value > n_rows - span:
            raise PropertySetError

        diff = value - self._value

        # Order is important, GtkTable does not allow us to have
        # a child which does not take up any space at all, eg
        # top-attach = bottom-attach
        cmd_bottom = CommandSetProperty(bottom, bottom.value + diff)
        cmd_top = CommandSetProperty(top, top.value + diff)
        if diff > 0:
            cmds = [cmd_bottom, cmd_top]
        else:
            cmds = [cmd_top, cmd_bottom]
        command_manager.execute(ContainerCommand(
            _('Moving widget to y position %d') % value, *cmds),
                                self.gadget.project, nested=False)

prop_registry.override_child_property('GtkTable::y-pos', YPos)

class ColSpan(CommonCustom):
    label = 'Colspan'
    minimum = 1
    priority = 3

    def _notify_update(self, gobj, pspec):
        parent = gobj.get_parent()
        self._update_lock = True
        self.set((parent.child_get_property(gobj, 'right-attach') -
                  parent.child_get_property(gobj, 'left-attach')))
        self._update_lock = False

    def load(self):
        object = self.object
        parent = self.object.get_parent()

        self._value = (parent.child_get_property(object, 'right-attach') -
                       parent.child_get_property(object, 'left-attach'))
        self.object.connect('child-notify::left-attach', self._notify_update)
        self.object.connect('child-notify::right-attach', self._notify_update)

    def _update_value(self, value):
        gadget = self.gadget
        n_columns = gadget.get_parent().get_prop('n-columns').value
        x_pos = gadget.get_child_prop('left-attach').value

        if value > n_columns - x_pos:
            raise PropertySetError

        right = gadget.get_child_prop('right-attach')
        command_manager.execute(
            CommandSetProperty(right, right.value + (value - self._value)),
            self.gadget.project,
            nested=False)

prop_registry.override_child_property('GtkTable::colspan', ColSpan)

class RowSpan(CommonCustom):
    label = 'Rowspan'
    minimum = 1
    priority = 4

    def _notify_update(self, gobj, pspec):
        parent = gobj.get_parent()
        self._update_lock = True
        self.set((parent.child_get_property(gobj, 'bottom-attach') -
                  parent.child_get_property(gobj, 'top-attach')))
        self._update_lock = False

    def load(self):
        object = self.object
        parent = self.object.get_parent()
        self._value = (parent.child_get_property(object, 'bottom-attach') -
                       parent.child_get_property(object, 'top-attach'))
        self.object.connect('child-notify::bottom-attach',
                            self._notify_update)
        self.object.connect('child-notify::top-attach',
                            self._notify_update)

    def _update_value(self, value):
        gadget = self.gadget
        n_rows = gadget.get_parent().get_prop('n-rows').value
        y_pos = gadget.get_child_prop('top-attach').value

        if value > n_rows - y_pos:
            raise PropertySetError

        bottom = gadget.get_child_prop('bottom-attach')
        command_manager.execute(
            CommandSetProperty(bottom, bottom.value + (value - self._value)),
            self.gadget.project,
            nested=False)

prop_registry.override_child_property('GtkTable::rowspan', RowSpan)
