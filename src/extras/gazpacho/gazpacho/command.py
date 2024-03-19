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

import gtk

from kiwi.component import get_utility

from gazpacho.app.bars import bar_manager
from gazpacho.i18n import _
from gazpacho.interfaces import IGazpachoApp

class Command(object):
    """A command is the minimum unit of undo/redoable actions.

    It has a description so the user can see it on the Undo/Redo
    menu items.

    Every Command subclass should implement the 'execute' method in
    the following way:
        - After a command is executed, if the execute method is called
        again, their effects will be undone.
        - If we keep calling the execute method, the action will
        be undone, then redone, then undone, etc...
        - To acomplish this every command constructor will probably
        need to gather more data that it may seems necessary.

    After you execute a command in the usual way you should put that
    command in the command stack of that project and that's what
    the push_undo method does. Otherwise no undo will be available.

    Some commands unifies themselves. This means that if you execute
    several commands of the same type one after the other, they will be
    treated as only one big command in terms of undo/redo. In other words,
    they will collapse. For example, every time you change a letter on a
    widget's name it is a command but all these commands unifies to one
    command so if you undo that all the name will be restored to the old one.
    """
    def __init__(self, description=None, ):
        self.description = description

    def __repr__(self):
        return '<Command %s>' % self.description

    def execute(self):
        """ This is the main method of the Command class.
        Note that it does not have any arguments so all the
        necessary data should be provided in the constructor.
        """
        pass

    def undo(self):
        """Convenience method that just call execute"""
        self.execute()

    def redo(self):
        """Convenience method that just call redo"""
        self.execute()

    def unifies(self, other):
        """True if self unifies with 'other'
        Unifying means that both commands can be treated as they
        would be only one command
        """
        return False

    def collapse(self, other):
        """Combine self and 'other' to form only one command.
        'other' should unifies with self but this method does not
        check that.
        """
        return False

class AccessorCommand(Command):
    """
    A simple Command which allows you to define a value to be set,
    a getter and a setter.
    """
    def __init__(self, description, value, setter, getter):
        """
        @param description: command description
        @param value: intial value to be set to the setter
        @param setter: a function taking one argument
        @param getter: a function returning a value and taking zero arguments.
        """
        Command.__init__(self, description)
        self._value = value
        self._setter = setter
        self._getter = getter

    def execute(self):
        oldvalue = self._getter()
        self._setter(self._value)
        self._value = oldvalue

class ContainerCommand(Command):
    """
    A command which can execute several other commands
    """
    def __init__(self, description, *commands):
        Command.__init__(self, description)
        self._commands = commands
        self._reverse = False

    def execute(self):
        commands = self._commands
        if self._reverse:
            commands = commands[::-1]

        for command in commands:
            command.execute()

        self._reverse = not self._reverse

class FlipFlopCommandMixin(object):
    """
    Base class for commands that alternatively call one method or another
    in their execute method based on a flipflop variable (two states)
    """

    def __init__(self, initial_value=True):
        self._state = initial_value

    def execute(self):
        if self._state:
            ret = self._execute_state1()
        else:
            ret = self._execute_state2()

        self._state = not self._state
        return ret

    def _execute_state1(self):
        """Subclasses should implement this method"""

    def _execute_state2(self):
        """Subclasses should implement this method"""


class CommandCreateDelete(FlipFlopCommandMixin, Command):
    def __init__(self, project, gadget, placeholder=None, parent=None,
                 create=True):
        FlipFlopCommandMixin.__init__(self, create)

        if create:
            description = _("Create %s") % gadget.name
        else:
            description = _("Delete %s") % gadget.name

        Command.__init__(self, description)

        self._project = project
        self._gadget = gadget
        self._placeholder = placeholder
        self._parent = parent
        self._initial_creation = create

    def _create_execute(self):
        from gazpacho.gadget import Gadget
        from gazpacho.placeholder import Placeholder

        gadget = self._gadget

        # Note that updating the dependencies might replace the
        # widget's gtk-widget so we need to make sure we refer to the
        # correct one afterward.
        gadget.deleted = False
        widget = gadget.widget

        if isinstance(widget, gtk.Window):

            # make window management easier by making created windows
            # transient for the editor window
            widget.set_transient_for(get_utility(IGazpachoApp).get_window())

            # Show windows earlier so we can restore the window-position
            # before the property editor is shown
            old_pos = widget.get_property('window-position')
            widget.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        else:
            if self._placeholder is None:
                for child in self._parent.widget.get_children():
                    if isinstance(child, Placeholder):
                        self._placeholder = child
                        break
            Gadget.replace(self._placeholder, widget, self._parent)

        self._gadget.project.add_widget(widget)
        self._gadget.select()

        widget.show_all()
        if isinstance(widget, gtk.Window):
            widget.set_position(old_pos)

            # we have to attach the accelerators groups so key shortcuts
            # keep working when this window has the focus. Only do
            # this the first time when creating a window, not when
            # redoing the creation since the accel group is already
            # set by then
            if self._initial_creation:
                widget.add_accel_group(bar_manager.get_accel_group())
                self._initial_creation = False

    _execute_state1 = _create_execute

    def _delete_execute(self):
        from gazpacho.gadget import Gadget
        from gazpacho.placeholder import Placeholder

        gadget = self._gadget

        if self._parent:
            if self._placeholder is None:
                self._placeholder = Placeholder()

            Gadget.replace(gadget.widget,
                           self._placeholder, self._parent)

        gadget.widget.hide()
        gadget.project.remove_widget(gadget.widget)
        gadget.deleted = True

    _execute_state2 = _delete_execute

