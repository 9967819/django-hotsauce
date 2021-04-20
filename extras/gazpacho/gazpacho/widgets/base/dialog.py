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

from gazpacho.placeholder import Placeholder
from gazpacho.properties import prop_registry
from gazpacho.gadget import Gadget
from gazpacho.widgetregistry import widget_registry
from gazpacho.widgets.base.window import WindowAdaptor

class DialogAdaptor(WindowAdaptor):
    def child_property_applies(self, context, ancestor, widget,
                               property_id):
        if property_id == 'response-id' and \
           isinstance(widget.parent, gtk.HButtonBox) and \
           isinstance(widget.parent.parent, gtk.VBox) and \
           widget.parent.parent.parent == ancestor:
            return True
        elif widget.parent == ancestor:
            return True

        return False

    def post_create(self, context, dialog, interactive=True):
        # set a reasonable default size for a dialog
        dialog.set_default_size(320, 260)

        # create the GladeWidgets for internal children
        self._setup_internal_children(dialog, context.get_project())

    def fill_empty(self, context, dialog):
        dialog.action_area.pack_start(Placeholder())
        dialog.action_area.pack_start(Placeholder())

        dialog.vbox.pack_start(Placeholder())

    def _setup_internal_children(self, dialog, project):
        child_class = widget_registry.get_by_name('GtkVBox')
        vbox_gadget = Gadget(child_class, project)
        vbox_gadget.setup_internal_widget(dialog.vbox, 'vbox',
                                          dialog.name or '')
        child_class = widget_registry.get_by_name('GtkHButtonBox')
        action_area_gadget = Gadget(child_class, project)
        action_area_gadget.setup_internal_widget(
            dialog.action_area,
            'action_area',
            dialog.name or '')
        self._init_property_meta_data(dialog)

    def _init_property_meta_data(self, dialog):
        """
        Set the metadata for some of the properties. This should not
        set default values of the properties since that is not always
        what we want.
        """
        # XXX not sure if we can assume that there actually is a vbox
        # and an action_area here?

        vbox = Gadget.from_widget(dialog.vbox)
        if vbox:
            vbox.get_prop('border-width').editable = False

        action_area = Gadget.from_widget(dialog.action_area)
        if action_area:
            action_area.get_prop('border-width').editable = False
            action_area.get_prop('spacing').editable = False

    def load(self, context, widget):
        gadget = super(WindowAdaptor, self).load(context, widget)
        self._init_property_meta_data(widget)
        return gadget

class MessageDialogAdaptor(DialogAdaptor):
    def post_create(self, context, dialog, interactive=True):
        dialog.set_default_size(400, 115)

# GtkDialog
prop_registry.override_simple('GtkDialog::has-separator', default=False)

