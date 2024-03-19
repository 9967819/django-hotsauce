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

import gtk

# External API, used by extensions. Do not remove.
def get_bool_from_string_with_default(value, default):
    if value in ['True', 'TRUE', 'true', 'yes', '1']:
        return True
    elif value in ['False', 'FALSE', 'false', 'no', '0']:
        return False
    else:
        return default

def get_parent(widget):
    from gazpacho.gadget import Gadget
    parent_widget = widget
    gadget = None
    while True:
        parent_widget = parent_widget.get_parent()
        if parent_widget is None:
            return None
        gadget = Gadget.from_widget(parent_widget)
        if gadget is not None:
            return gadget

    return None

def select_iter(treeview, item_iter):
    """
    @param treeview:
    @param item_iter:
    """
    model = treeview.get_model()
    path = model[item_iter].path
    if treeview.flags() & gtk.REALIZED:
        treeview.expand_to_path(path)
        treeview.scroll_to_cell(path)
    treeview.get_selection().select_path(path)

def get_all_children(container):
    """This function get all children of a container, included its internal
    children"""
    children = []
    def fetch_child(child, bag):
        bag.append(child)
    container.forall(fetch_child, children)
    return children
