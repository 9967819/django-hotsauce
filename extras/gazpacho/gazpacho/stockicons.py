# Copyright (C) 2004,2005 by SICEm S.L.
#               2006 by Async Open Source
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

import gtk
from kiwi.environ import environ
from kiwi.python import Settable
from kiwi.ui.dialogs import BaseDialog
from kiwi.ui.objectlist import ObjectList, Column
from kiwi.utils import gsignal, type_register

from gazpacho.constants import MISSING_ICON, STOCK_SIZEGROUP
from gazpacho.i18n import _

(STOCK_ID,
 STOCK_LABEL) = list(range(2))

_stock_icons = []

def create_stock_icon(iconfile, stock_id, icon_factory=None):
    if not icon_factory:
        icon_factory = gtk.IconFactory()

    icon_source = gtk.IconSource()
    icon_source.set_filename(iconfile)
    icon_set = gtk.IconSet()
    icon_set.add_source(icon_source)
    icon_factory.add(stock_id, icon_set)

    return icon_factory

def register_stock_icons():
    """
    Register the custom stock icons used by gazpacho
    """
    icon_factory = None

    for fname, stock_id in [('gazpacho-icon.png', MISSING_ICON),
                            ('sizegroup-both.png', STOCK_SIZEGROUP)]:
        filename = environ.find_resource('pixmap', fname)
        icon_factory = create_stock_icon(filename, stock_id, icon_factory)

    icon_factory.add_default()

def get_stock_icons():
    """
    Get a sorted list of all available stock icons
    @returns: a list of tuples; (stock_label, stock_id)
    """

    global _stock_icons
    if _stock_icons:
        return _stock_icons

    icons = []

    for stock_id in gtk.stock_list_ids():
        # Do not list stock ids starting with gazpacho-, they
        # are considered private
        if stock_id.startswith('gazpacho-'):
            continue

        stock_info = gtk.stock_lookup(stock_id)
        if not stock_info:
            # gtk-new -> New
            if stock_id.startswith('gtk-'):
                stock_label = stock_id[4:].replace('-', ' ')
            else:
                stock_label = stock_id
            stock_label = stock_label.capitalize()
        else:
            stock_label = stock_info[1].replace('_', '')

        icons.append((stock_label, stock_id))

    icons.sort()
    _stock_icons = icons

    return icons

class StockIconList(gtk.HBox):
    """
    I am a helper to manage stock icons
    """

    gsignal('changed', str)

    def __init__(self):
        gtk.HBox.__init__(self)

        self._model = gtk.ListStore(str, str)
        self._populate_icons()

        self._create_ui()

    def _create_ui(self):
        self._preview = gtk.Image()
        self._preview.set_sensitive(False)
        self.pack_start(self._preview, False, False, 6)

        self._stock = gtk.ComboBoxEntry(self._model)
        self._stock.clear()
        self._stock.connect('changed', self._on_stock_id_changed)
        self._stock.set_sensitive(False)
        self._stock.set_wrap_width(5)

        renderer = gtk.CellRendererPixbuf()
        renderer.set_property('xalign', 0.0)
        self._stock.pack_start(renderer)
        self._stock.add_attribute(renderer, 'stock-id', STOCK_ID)

        renderer = gtk.CellRendererText()
        renderer.set_property('xalign', 0.0)
        self._stock.pack_start(renderer)
        self._stock.add_attribute(renderer, 'text', STOCK_LABEL)

        self.pack_start(self._stock, False, False)

    def _populate_icons(self):
        model = self._model

        for stock_label, stock_id in get_stock_icons():
            model.append((stock_id, stock_label))

    def _on_stock_id_changed(self, combobox):
        stock_id = self._stock.child.get_text()
        if not stock_id in get_stock_icons():
            stock_id = MISSING_ICON

        self._preview.set_from_stock(stock_id, gtk.ICON_SIZE_BUTTON)
        self.emit('changed', stock_id)

    def set_sensitive(self, sensitive):
        """
        Sets the stock icon list to sensitive
        @param sensitive: True if sensitive
        @type sensitive: boolean
        """
        self._preview.set_sensitive(sensitive)
        self._stock.set_sensitive(sensitive)

    def reset(self):
        """
        Resets the senstivty and selects the first item
        """
        self._stock.set_active(0)
        self.set_sensitive(False)

    def set_stock_id(self, stock_id):
        """
        Sets a stock icon id from a string
        @param stock_id: stock icon id
        @type stock_id: string
        """
        if not stock_id in get_stock_icons():
            preview = MISSING_ICON
        else:
            for row in self._model:
                if row[STOCK_ID] == stock_id:
                    self._stock.set_active_iter(row.iter)
                    break
            else:
                raise AssertionError
            preview = stock_id

        self._stock.child.set_text(stock_id)
        self._preview.set_from_stock(preview, gtk.ICON_SIZE_BUTTON)

    def get_stock_id(self):
        """
        @returns: the current stock id
        """
        return self._stock.child.get_text()

type_register(StockIconList)

class StockIconDialog(BaseDialog):
    def __init__(self, parent=None):
        BaseDialog.__init__(self, parent, title=_('Stock Icons'),
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.set_size_request(260, 330)

        self._stockicons = ObjectList([Column('stock_id', use_stock=True),
                                       Column('name')])
        self._stockicons.set_headers_visible(False)
        self._stockicons.connect('row-activated',
                                 self._on_stockicons__row_activated)
        self._icons = {}
        for stock_label, stock_id in get_stock_icons():
            icon = Settable(stock_id=stock_id, name=stock_label)
            self._stockicons.append(icon)
            self._icons[stock_id] = icon

        self.vbox.pack_start(self._stockicons)
        self._stockicons.show()

    def select(self, value):
        icon = self._icons.get(value)
        if icon:
            self._stockicons.select(icon)

    def get_selected(self):
        icon = self._stockicons.get_selected()
        if icon:
            return icon.stock_id

    def _on_stockicons__row_activated(self, objectlist, icon):
        self.emit('response', gtk.RESPONSE_OK)
