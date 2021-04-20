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

import gobject
import gtk

class CommandView(gtk.ScrolledWindow):
    """
    This class is just a little TreeView that knows how
    to show the command stack of a project.
    It shows a plain list of all the commands performed by
    the user and also it mark the current command that
    would be redone if the user wanted so.
    Older commands are under newer commands on the list.
    """
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self._project = None

        self._model = gtk.ListStore(bool, str)
        self._treeview = gtk.TreeView(self._model)
        self._treeview.set_headers_visible(False)

        column = gtk.TreeViewColumn()
        renderer1 = gtk.CellRendererPixbuf()
        column.pack_start(renderer1, expand=False)
        column.set_cell_data_func(renderer1, self._draw_redo_position)

        renderer2 = gtk.CellRendererText()
        column.pack_start(renderer2, expand=True)
        column.add_attribute(renderer2, 'text', 1)

        self._treeview.append_column(column)

        self.add(self._treeview)

    def set_project(self, project):
        self._project = project
        self.update()

    def update(self):
        self._model.clear()
        if self._project is None:
            return

        undos = self._project.undo_stack.get_undo_commands()
        if undos:
            for cmd in undos[:-1]:
                self._model.insert(0, (False, cmd.description))
            self._model.insert(0, (True, undos[-1].description))

        for cmd in self._project.undo_stack.get_redo_commands():
            self._model.insert(0, (False, cmd.description))

    def _draw_redo_position(self, column, cell, model, iter):
        is_the_one = model[iter][0]

        if is_the_one:
            stock_id = gtk.STOCK_JUMP_TO
        else:
            stock_id = None

        cell.set_property('stock-id', stock_id)

gobject.type_register(CommandView)
