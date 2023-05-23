# Copyright (C) 2006 by Nokia Corporation
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

from gazpacho.commandmanager import command_manager

# This module contains very high level handy functions
# that are just wrappers around internal gazpacho machinery
#
# It should be easy to import this module from anyware so
# local imports in these functions are not only allowed but
# recommended to avoid dependency cycles
#
# This module is similar to the zapi module in Zope 3

def create_gadget(project, adaptor, placeholder=None, parent=None,
                  interactive=True):
    """
    Creates a gadget and add it to a project.

    Basically it does all of the following:

      1. Create the Gtk+ object

      2. Wrap it in a Gadget

      3. Add it to a project

      4. Make all the process undoable by using a command

    @param project: The project the gadget will be added to
    @type project: gazpacho.project.Project
    @param adaptor: The widget adaptor that will be used to create and wrapp
      the widget
    @type adaptor: subclass of gazpacho.widgetadaptor.WidgetAdaptor
    @param placeholder: the placeholder that will be replaced by the gadget.
      It can be None if the adaptor is for a toplevel widget
    @type placeholder: gazpacho.placeholder.Placeholder
    @param parent: the parent of the gadget it's going to be created. It can
      be None for widgets that don't have a parent (e.g. toplevels)
    @type parent: gazpacho.gadget.Gadget
    @param interactive: this boolean indicates if the user can be prompted
      for additional options while creating the gadget. For tests it should
      be False
    @type interactive: boolean
    @return: the gadget that was created
    @rtype: gazpatcho.widget.Gadget
    """
    from gazpacho import util
    from gazpacho.command import CommandCreateDelete
    from gazpacho.palette import palette
    from gazpacho.widgetadaptor import CreationCancelled

    if placeholder:
        parent = util.get_parent(placeholder)
        if parent is None:
            return

    if project is None:
        project = parent.project

    gadget = None
    try:
        gadget = _create_gadget(project, adaptor, interactive)
    except CreationCancelled:
        return

    cmd = CommandCreateDelete(project, gadget, placeholder, parent, True)
    command_manager.execute(cmd, project)

    if not palette.persistent_mode:
        palette.unselect_widget()

    if not isinstance(gadget.widget, gtk.Window):
        gadget.get_prop('visible').value = True

    return gadget

def delete_gadget(project, gadget):
    """
    Delete a gadget

    Delete a gadget and remove it from the project. Note that the gadget won't
    probably be destroyed for undo purposes

    @param project: The project the gadget belongs to
    @type project: gazpacho.project.Project
    @param gadget: the gadget to be removed
    @type gadget: gazpacho.gadget.Gadget
    """
    # internal children cannot be deleted. Should we notify the user?
    if gadget.internal_name is not None:
        return

    if isinstance(gadget.widget, gtk.TreeViewColumn):
        from gazpacho.util import get_parent
        from gazpacho.widgets.base.treeview import CommandAddRemoveTreeViewColumn
        tree_view = get_parent(gadget.widget)
        cmd = CommandAddRemoveTreeViewColumn(tree_view, gadget, project, False)
    else:
        from gazpacho.command import CommandCreateDelete
        cmd = CommandCreateDelete(project, gadget, None, gadget.get_parent(),
                                  False)

    command_manager.execute(cmd, project)

# Private internal functions

def _create_gadget(project, adaptor, interactive):
    from gazpacho.gadget import Gadget
    gadget = Gadget(adaptor, project)
    gadget.create_widget(interactive)
    return gadget
