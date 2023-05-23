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

class CommandManager(object):
    """
    This class is the entry point accesing the commands.
    Every undoable action in Gazpacho is wrapped into a command.
    The stack of un/redoable actions is stored in the Project class
    so each project is independent on terms of undo/redo.
    """

    def __init__(self):
        self._in_progress = False

    def undo(self, project):
        """Undo the last command if there is such a command"""
        if project.undo_stack.has_undo():
            cmd = project.undo_stack.pop_undo()
            cmd.undo()

    def redo(self, project):
        """Redo the last undo command if there is such a command"""
        if project.undo_stack.has_redo():
            cmd = project.undo_stack.pop_redo()
            cmd.redo()

    def execute(self, cmd, project, nested=True):
        self._in_progress = True
        ret = cmd.execute()

        # If nested is set to true and we're already executing another
        # command, don't add it to the undo/redo list
        # This is a big hack, but we need a transactional like API to
        # solve it properly
        if nested or not self._in_progress:
            project.undo_stack.push_undo(cmd)
        self._in_progress = True
        return ret

command_manager = CommandManager()
