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

from gazpacho import util

from gazpacho.clipboard import CommandCutPaste
from gazpacho.command import Command, FlipFlopCommandMixin
from gazpacho.gadget import Gadget
from gazpacho.i18n import _
from gazpacho.placeholder import Placeholder
from gazpacho.properties import prop_registry, CustomProperty, IntType
from gazpacho.util import get_parent
from gazpacho.widgets.base.base import ContainerAdaptor
from gazpacho.widgetregistry import widget_registry

class BoxAdaptor(ContainerAdaptor):
    def fill_empty(self, context, widget):
        pass

# GtkBox
class BoxSizeProp(CustomProperty, IntType):
    minimum = 1
    default = 3
    label = 'Size'
    persistent = False

    def __init__(self, object):
        super(BoxSizeProp, self).__init__(object)

    def load(self):
        self._initial = self.default

        # Don't set default if object has childs already
        if not self.get():
            self.set(self.default)

    def get(self):
        return len(self.object.get_children())

    def set(self, new_size):
        old_size = len(self.object.get_children())
        if new_size == old_size:
            return
        elif new_size > old_size:
            # The box has grown. Add placeholders
            while new_size > old_size:
                self.object.add(Placeholder())
                old_size += 1
        elif new_size > 0:
            # The box has shrunk. Remove placeholders first, starting
            # with the last one
            for child in self.object.get_children()[::-1]:
                if isinstance(child, Placeholder):
                    gtk.Container.remove(self.object, child)
                    old_size -= 1

                if old_size == new_size:
                    return

            # and then remove widgets
            child = self.object.get_children()[-1]
            while old_size > new_size and child:
                gadget = Gadget.from_widget(child)
                if gadget: # It may be None, e.g a placeholder
                    gadget.project.remove_widget(child)

                gtk.Container.remove(self.object, child)
                child = self.object.get_children()[-1]
                old_size -= 1
        self.notify()

prop_registry.override_property('GtkBox::size', BoxSizeProp)
prop_registry.override_simple('GtkBox::spacing', minimum=0)

class AppendGadgetCommand(Command):
    """
    Command for adding a widget to a box. This command isn't inteded
    to be used directly but to be subclasses by other commands.
    """

    def __init__(self, source_gadget, box, pos, description=None):
        """
        Initialize the command. Note that the source_gadget has to be
        a new widget that is not already in use in the project.

        @param source_gadget: the widget that is to be inserted
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param box: the box into which the widget should be inserted
        @type box: L{gazpacho.gadget.Gadget}
        @param pos: the position where the widget will be inserted
        @type pos: int
        """
        Command.__init__(self, description)

        self._box = box.widget
        self._pos = pos
        self._source = source_gadget.widget
        self._project = box.project


    def insert_execute(self):
        """
        Insert the widget into the box.
        """
        self._box.add(self._source)
        self._box.reorder_child(self._source, self._pos)

        self._project.add_widget(self._source)
        self._project.selection.set(self._source)
        self._source.show_all()

    def remove_execute(self):
        """
        Remove the widget from the box.
        """
        self._box.remove(self._source)
        self._source.hide()
        self._project.remove_widget(self._source)

class DragAppendCommand(AppendGadgetCommand):
    """
    Append a copy of an existing widget to a box. It's optional to
    remove the source widget as well.
    """

    def __init__(self, source_gadget, box, pos, keep_source):
        """
        Initialize the command.

        @param source_gadget:
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param box: the box into which the widget should be inserted
        @type box: L{gazpacho.gadget.Gadget}
        @param pos: the position where the widget will be inserted
        @type pos: int
        """
        description = _("Drag - append")

        # We append a copy of the widget
        source_copy = source_gadget.copy(box.project, not keep_source)
        AppendGadgetCommand.__init__(self, source_copy, box, pos, description)

        self._undo = False

        # Reuse the Cut command for removing the widget
        self._remove_cmd = None
        if not keep_source:
            self._remove_cmd = CommandCutPaste(source_gadget,
                                               source_gadget.project,
                                               None,
                                               True)

    def execute(self):
        """
        Execute the command.
        """
        if self._undo:
            self.remove_execute()

        if self._remove_cmd:
            self._remove_cmd.execute()

        if not self._undo:
            self.insert_execute()

        self._undo = not self._undo

class CreateAppendCommand(AppendGadgetCommand):
    """
    Append a newly created widget to a box.
    """

    def __init__(self, source_gadget, box, pos):
        """
        Initialize the command.

        @param source_gadget:
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param box: the box into which the widget should be inserted
        @type box: L{gazpacho.gadget.Gadget}
        @param pos: the position where the widget will be inserted
        @type pos: int
        """
        description = _("Create - extend")
        AppendGadgetCommand.__init__(self, source_gadget, box, pos, description)
        self._undo = False

    def execute(self):
        """
        Execute the command.
        """
        if self._undo:
            self.remove_execute()
        else:
            self.insert_execute()

        self._undo = not self._undo


class ExtendGadgetCommand(Command):
    """
    Command for replacing a target widget with a box containing a copy
    of both the target and the source.
    """

    def __init__(self, source_gadget, target_gadget, location,
                 description=None):
        """
        Initialize the command. Note that the source_gadget has to be
        a new widget that is not already in use in the project.

        @param source_gadget: the widget to add
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param target_gadget: the widget to replace
        @type target_gadget: L{gazpacho.gadget.Gadget}
        @param location: Where to put the source in relation to the target
        @type location: (constant value)
        """
        Command.__init__(self, description)

        self._project = target_gadget.project
        self._gtk_source = source_gadget.widget
        self._gtk_target = target_gadget.widget

        # Create the box with a copy of the target
        target_copy = target_gadget.copy(keep_name=True)

        self._gtk_box = self._create_box(source_gadget.widget,
                                         target_copy.widget, location)


    def _create_box(self, gtk_source, gtk_target, location):
        """
        Create a Box containing the widgets.

        @param gtk_source: the gtk  widget to add
        @type gtk_source: gtk.Gadget
        @param gtk_target: the gtk widget to replace
        @type gtk_target: gtk.Gadget
        @param location: Where to put the source in relation to the target
        @type location: (constant value)
        """
        from gazpacho.dndhandlers import DND_POS_TOP, DND_POS_BOTTOM, \
             DND_POS_LEFT

        # Create a Box with size 2
        if location in [DND_POS_TOP, DND_POS_BOTTOM]:
            box_type = 'GtkVBox'
        else:
            box_type = 'GtkHBox'
        adaptor = widget_registry.get_by_name(box_type)
        box_gadget = Gadget(adaptor, self._project)
        box_gadget.create_widget(interactive=False)
        box_gadget.get_prop('size').set(2)

        # Add the source and target widgets
        children = box_gadget.widget.get_children()
        if location in [DND_POS_TOP, DND_POS_LEFT]:
            source_placeholder, target_placeholder = children[0], children[1]
        else:
            source_placeholder, target_placeholder = children[1], children[0]

        Gadget.replace(source_placeholder, gtk_source, box_gadget)
        Gadget.replace(target_placeholder, gtk_target, box_gadget)

        return box_gadget.widget

    def _replace(self, target, source):
        """
        Replace the target widget with the source widget.

        @param target: the target gtk widget
        @type target: gtk.Gadget
        @param source: the source gtk widget
        @type source: gtk.Gadget
        """
        parent = util.get_parent(target)
        Gadget.replace(target, source, parent)

        # Remove old widget
        target.hide()
        self._project.remove_widget(target)

        # Add new widget
        self._project.add_widget(source)
        source.show_all()

    def add_box(self):
        """
        Replace the original target widget with the box.
        """
        self._replace(self._gtk_target, self._gtk_box)
        self._project.selection.set(self._gtk_source)

    def remove_box(self):
        """
        Replace the box with the original target widget.
        """
        self._replace(self._gtk_box, self._gtk_target)
        self._project.selection.set(self._gtk_target)

class DragExtendCommand(ExtendGadgetCommand):
    """
    Command for replacing a target widget with a box containing a copy
    of both the target and the source.
    """

    def __init__(self, source_gadget, target_gadget, location, keep_source):
        """
        Initialize the command.

        @param source_gadget: the widget to add
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param target_gadget: the widget to replace
        @type target_gadget: L{gazpacho.gadget.Gadget}
        @param location: Where to put the source in relation to the target
        @type location: (constant value)
        @param keep_source: if true we should not remove the source
        widget, if false we should.
        @type keep_source: bool
        """
        source_copy = source_gadget.copy(target_gadget.project,
                                         not keep_source)
        ExtendGadgetCommand.__init__(self, source_copy, target_gadget, location,
                                     _("Drag - extend"))

        self._undo = False
        self._remove_cmd = None

        # Reuse the Cut command for removing the widget
        if not keep_source:
            self._remove_cmd = CommandCutPaste(source_gadget,
                                               source_gadget.project,
                                               None,
                                               True)

    def execute(self):
        """
        Execute the command.
        """
        if self._undo:
            self.remove_box()

        if self._remove_cmd:
            self._remove_cmd.execute()

        if not self._undo:
            self.add_box()

        self._undo = not self._undo

class CreateExtendCommand(ExtendGadgetCommand):
    """
    Command for replacing a target widget with a box containing a copy
    of both the target and the source.
    """

    def __init__(self, source_gadget, target_gadget, location):
        """
        Initialize the command.

        @param source_gadget: the widget to add
        @type source_gadget: L{gazpacho.gadget.Gadget}
        @param target_gadget: the widget to replace
        @type target_gadget: L{gazpacho.gadget.Gadget}
        @param location: Where to put the source in relation to the target
        @type location: (constant value)
        @param keep_source: if true we should not remove the source
        widget, if false we should.
        @type keep_source: bool
        """
        ExtendGadgetCommand.__init__(self, source_gadget, target_gadget,
                                     location, _("Create - extend"))
        self._undo = False

    def execute(self):
        """
        Execute the command.
        """
        if self._undo:
            self.remove_box()

        if not self._undo:
            self.add_box()

        self._undo = not self._undo

class CommandBoxInsertPlaceholder(FlipFlopCommandMixin, Command):
    """
    Insert a placeholder before or after the specified position
    in the box.
    """

    def __init__(self, box, pos, after):

        FlipFlopCommandMixin.__init__(self, True)

        if after:
            description = _("Insert after")
            pos += 1
        else:
            description = _("Insert before")

        Command.__init__(self, description)

        self._box = box
        self._pos = pos
        self._placeholder = None

    def _insert_execute(self):
        # create a placeholder and insert it at self._pos
        self._placeholder = Placeholder()
        self._box.widget.add(self._placeholder)
        self._box.widget.reorder_child(self._placeholder, self._pos)
    _execute_state1 = _insert_execute

    def _delete_execute(self):
        self._placeholder.destroy()
        self._placeholder = None
    _execute_state2 = _delete_execute

class CommandBoxDeletePlaceholder(Command):
    def __init__(self, placeholder):
        Command.__init__(self, description = _("Delete placeholder"))

        parent = get_parent(placeholder)

        self._project = parent.project
        self._placeholder = placeholder
        self._gtk_parent = parent.widget
        self._create = False

        children = self._gtk_parent.get_children()
        self._pos = children.index(placeholder)

    def _create_execute(self):
        """
        Insert the placeholder at self._pos.
        """
        self._gtk_parent.add(self._placeholder)
        self._gtk_parent.reorder_child(self._placeholder, self._pos)

    def _delete_execute(self):
        """
        Remove the placeholder.
        """
        self._gtk_parent.remove(self._placeholder)
        self._project.selection.clear()

    def execute(self):
        if self._create:
            self._create_execute()
        else:
            self._delete_execute()

        self._create = not self._create

