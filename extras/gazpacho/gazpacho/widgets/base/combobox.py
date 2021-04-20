# Copyright (C) 2005 by SICEm S.L. and Async Open Source
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

from gazpacho.loader.custom import combobox_set_content_from_string
from gazpacho.properties import prop_registry, CustomProperty, StringType
from gazpacho.widgetadaptor import WidgetAdaptor

class ComboBoxAdaptor(WidgetAdaptor):
    def create(self, context, interactive=True):
        combo = super(ComboBoxAdaptor, self).create(context, interactive)
        model = gtk.ListStore(gobject.TYPE_STRING)
        combo.set_model(model)
        return combo

    def fill_empty(self, context, widget):
        pass

# GtkComboBox

# XXX: This is too complex, fix properties API
#      TransparentProperty doesn't work, why?
class Items(CustomProperty, StringType):
    label = 'Items'
    default = ''
    def load(self):
        model = self.object.get_model()
        if not model:
            # Hack warning, only needed for GtkComboBoxEntry
            model = gtk.ListStore(str)
            self.object.set_model(model)
        self._value = '\n'.join([row[0] for row in model])
        self._initial = self.default

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        combobox_set_content_from_string(self.object, value)
prop_registry.override_property('GtkComboBox::items', Items)

# These properties are buggy in GTK+ 2.4
prop_registry.override_simple('GtkComboBox::column-span-column', editable=False)
prop_registry.override_simple('GtkComboBox::row-span-column', editable=False)

# GtkComboBoxEntry
prop_registry.override_simple('GtkComboBoxEntry::text-column', default=0)

