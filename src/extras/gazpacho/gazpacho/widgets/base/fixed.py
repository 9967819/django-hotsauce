# Copyright (C) 2005 by SICEm S.L.
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

from gazpacho import gapi
from gazpacho.cursor import Cursor
from gazpacho.gadget import Gadget
from gazpacho.widgets.base.base import ContainerAdaptor

class FixedAdaptor(ContainerAdaptor):
    def __init__(self):
        # save the last button click coordinate
        self.x = 0
        self.y = 0

    def post_create(self, context, fixed, interactive=True):
        fixed.connect('expose-event', self.on_expose_event)

    def replace_child(self, context, current, new, container):
        "'current' is always None for Fixed since it never has any placeholder"
        container.put(new, self.x, self.y)

    def button_release(self, context, fixed, event):
        # we remember the point where the user clicked
        toplevel = fixed.get_toplevel()
        if toplevel:
            self.x, self.y = toplevel.translate_coordinates(fixed,
                                                            int(event.x),
                                                            int(event.y))

        # if there is some widget selected in the palette it's time to add it
        project = context.get_project()
        if project._app.add_class:
            gadget = Gadget.from_widget(fixed)
            gapi.create_gadget(project, project.get_app().add_class,
                               None, gadget)
        return False

    def motion_notify(self, context, fixed, event):
        app = context.get_project()._app
        Cursor.set_for_widget_adaptor(event.window, app.add_class)
        return False

    def on_expose_event(self, fixed, event):
        # draw a grid
        window = fixed.window
        bw = fixed.get_property('border-width')
        w, h = window.get_size()
        gc = fixed.style.dark_gc[gtk.STATE_NORMAL]
        for gridx in range(bw, w-bw, 10):
            for gridy in range(bw, h-bw, 10):
                window.draw_point(gc, gridx, gridy)

        return False

