# Copyright (C) 2005 by Mattias Karlsson
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

import gobject
import gtk
from kiwi.utils import gsignal, type_register
from kiwi.component import implements

from gazpacho.interfaces import IReferencable

class GSizeGroup(gobject.GObject):

    implements(IReferencable)

    gsignal('name-changed')
    gsignal('gadgets-added', object)
    gsignal('gadgets-removed', object)

    def __init__(self, name, group, gadgets=[]):
        """
        Initialize the sizegroup.

        @param name: the name
        @type name: str
        @param group: sizegroup
        @type group: a gtk.SizeGroup
        """
        gobject.GObject.__init__(self)

        if not isinstance(group, gtk.SizeGroup):
            raise TypeError("group must be a gtk.SizeGroup, not %r" % group)

        self._name = name
        self._gtk_sizegroup = group
        self._gadgets = gadgets or [] # XXX: fixme

    #
    # Properties
    #
    def _set_name(self, name):
        """
        Set the sizegroup name.

        @param name: the name
        @type name: str
        """
        self._name = name
        self.emit('name_changed')

    def _get_name(self):
        """
        Get the sizegroup name.

        @return: the sizegroup name
        @rtype: str
        """
        return self._name

    name = property(_get_name, _set_name)

    def _set_mode(self, mode):
        """
        Set the sizegroup mode.

        @param mode: the sizegroup mode
        @type mode: constants, see gtk.SizeGroup
        """
        self._gtk_sizegroup.set_mode(mode)
        self.emit('name-changed')

    def _get_mode(self):
        """
        Get the SizeGroup mode.

        @return: the sizegroup mode
        @rtype: constants, see gtk.SizeGroup
        """
        return self._gtk_sizegroup.get_mode()

    mode = property(_get_mode, _set_mode)

    #
    # Public methods
    #
    def is_empty(self):
        """
        Check if the sizegroup is empty

        @return: true if the sizegroup doesn't have any gadgets
        @rtype: bool
        """
        return not self._gadgets

    def has_gadget(self, gadget):
        """
        Check if the size group has the gadget.

        @param gadget: the gadget to test
        @type gadget: gazpacho.gadget.Widget

        @return: true if the gadget is in the group
        @rtype: bool
        """
        return gadget in self._gadgets

    def get_gadgets(self):
        """
        Get the gadgets for this group.

        @return: the gadgets
        @rtype: list (of gazpacho.gadget.Widget)
        """
        return self._gadgets[:]

    def add_gadgets(self, gadgets):
        """
        Add gadgets to the SizeGroup.

        @param gadgets: the gadgets to add
        @type gadgets: list (of gazpacho.gadget.Widget)
        """
        if not gadgets:
            return

        self._gadgets += gadgets
        for gadget in gadgets:
            gadget.references.add_referrer(self)
            prop = gadget.get_prop('sizegroup')
            prop.value = self._name
            self._add_widget(gadget.widget)

        self.emit('gadgets-added', gadgets)

    def remove_gadgets(self, gadgets):
        """
        Remove gadgets from the sizegroup.

        @param gadgets: the gadgets to remove
        @type gadgets: list (of gazpacho.gadget.Widget)
        """
        if not gadgets:
            return

        for gadget in gadgets:
            gadget.references.remove_referrer(self)
            self._gadgets.remove(gadget)
            self._remove_widget(gadget.widget)
            prop = gadget.get_prop('sizegroup')
            prop.value = None

        self.emit('gadgets-removed', gadgets)

    # IReferencable
 
    def remove_reference(self, gadget):
        """
        See L{gazpacho.interfaces.IReferencable.remove_reference}
        """
        self._gadgets.remove(gadget)
        prop = gadget.get_prop('sizegroup')
        prop.value = None
        self._remove_widget(gadget.widget)
        self.emit('gadgets-removed', [gadget])
 
    def add_reference(self, gadget):
        """
        See L{gazpacho.interfaces.IReferencable.add_reference}
        """
        self._gadgets.append(gadget)
        prop = gadget.get_prop('sizegroup')
        prop.value = self._name
        self._add_widget(gadget.widget)
        self.emit('gadgets-added', [gadget])

    #
    # Private methods
    #
    def _add_widget(self, widget):
        """
        Add a gtk widget to the gtk SizeGroup.

        @param widget: the gtk widget
        @type widget: gtk.Widget
        """
        self._gtk_sizegroup.add_widget(widget)

    def _remove_widget(self, widget):
        """
        Remove a gtk widget from the gtk SizeGroup.

        @param widget: the gtk widget
        @type widget: gtk.Widget
        """
        self._gtk_sizegroup.remove_widget(widget)

type_register(GSizeGroup)

def safe_to_add_gadgets(sizegroup, gadgets):
    """
    Test if it is safe to add the gadgets to the sizegroup. Gadgets
    who has an ancestor or child in the sizegroup cannot be
    added.

    @param sizegroup: the size group
    @type sizegroup: L{gazpacho.sizegroup.GSizeGroup}
    """
    all_gadgets = sizegroup.get_gadgets() + gadgets

    # Create gadget parent cache
    parents = {}
    for gadget in all_gadgets:
        parent = gadget.get_parent()
        while parent:
            if parent in parents:
                break
            parents[parent] = parent
            parent = parent.get_parent()

    for gadget in all_gadgets:
        if gadget in parents:
            return False

    return True
