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

from gazpacho.properties import prop_registry, CustomProperty, StringType
from gazpacho.widgets.base.base import ContainerAdaptor

class TextViewAdaptor(ContainerAdaptor):
    def fill_empty(self, context, gadget):
        pass

class TextProp(CustomProperty, StringType):
    def get(self):
        buffer = self.object.get_buffer()
        (start, end) = buffer.get_bounds()
        return buffer.get_text(start, end, False)

    def set(self, value):
        buffer = self.object.get_buffer()
        buffer.set_text(value or '')

prop_registry.override_property('GtkTextView::text', TextProp)
