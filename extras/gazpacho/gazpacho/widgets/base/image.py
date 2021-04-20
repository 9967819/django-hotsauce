# Copyright (C) 2004,2005 by SICEm S.L. and Imendio AB
#               2005,2006 Async Open Source
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
from gazpacho.propertyeditor import EditorPropertyImage, EditorPropertyStock

class FileProp(CustomProperty, StringType):
    # we can remove this class when depending in gtk 2.8 since this property
    # is readable there
    editable = True
    translatable = False

    editor = EditorPropertyImage

    # We need to override get_default, since
    # the standard mechanism to get the initial value
    # is calling get_property, but ::file is not marked as readable
    def get_default(self, gobj):
        return ""

    def load(self):
        value = super(FileProp, self).load()
        self._initial = value
        self.set(value)

    def get(self):
        return self.object.get_data('image-file-name')

    def set(self, value):
        if value:
            self.object.set_data('image-file-name', value)
            self.object.set_property('file', value)

    def save(self):
        return self.get()

prop_registry.override_simple('GtkImage::file', FileProp)

class StockProp(CustomProperty, StringType):
    default = "gtk-missing-image"
    translatable = False
    editor = EditorPropertyStock
    def save(self):
        if self.object.get_data('image-file-name'):
            return
        return super(StockProp, self).save()

prop_registry.override_simple('GtkImage::stock', StockProp)
