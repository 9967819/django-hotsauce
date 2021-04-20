# Copyright (C) 2005,2006 Johan Dahlin
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

"""
Loader hacks specific for Gazpacho the application.
"""

import gtk

from gazpacho.loader.loader import ObjectBuilder
from gazpacho.loader.custom import ButtonAdapter, DialogAdapter, \
     WindowAdapter, str2bool, adapter_registry
from gazpacho.placeholder import Placeholder
from gazpacho.widgets.base.custom import Custom

class GazpachoButtonAdapter(ButtonAdapter):
    def add(self, parent, child, properties, type):
        # This is a hack, remove when the button saving/loading code
        # is improved
        for cur_child in parent.get_children():
            parent.remove(cur_child)
        ButtonAdapter.add(self, parent, child, properties, type)

class GazpachoWindowAdapter(WindowAdapter):
    object_type = gtk.Window
    def prop_set_visible(self, window, value):
        window.set_data('gazpacho::visible', str2bool(value))

    def prop_set_modal(self, window, value):
        window.set_data('gazpacho::modal', str2bool(value))

adapter_registry.register_adapter(GazpachoWindowAdapter)

# FIXME: This is quite strange, but apparently we need this too.
class GazpachoDialogAdapter(DialogAdapter):
    object_type = gtk.Dialog
    def prop_set_modal(self, window, value):
        window.set_data('gazpacho::modal', str2bool(value))

adapter_registry.register_adapter(GazpachoDialogAdapter)

class GazpachoObjectBuilder(ObjectBuilder):
    def __init__(self, **kwargs):
        self._app = kwargs.pop('app', None)
        kwargs['placeholder'] = self.create_placeholder
        kwargs['custom'] = Custom

        # We want to ignore the domain, otherwise we will end up
        # with a /translated/ interface inside gazpacho itself.
        kwargs['ignore_domain'] = True
        ObjectBuilder.__init__(self, **kwargs)

    def create_placeholder(self, name):
        return Placeholder()

    def show_windows(self):
        pass
