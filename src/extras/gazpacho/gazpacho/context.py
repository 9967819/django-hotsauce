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

from kiwi.component import get_utility

from gazpacho.interfaces import IGazpachoApp

class Context:
    """This class expose the functionality of Gazpacho that plugins are
    allowed to use.

    There is one context object for every project.
    """
    def __init__(self, project):
        # project is private because we don't want plugins to mess up with
        # the cool stuff
        self.__project = project

    def get_application_window(self):
        """This is useful to show dialogs."""
        return get_utility(IGazpachoApp).get_window()

    def get_project(self):
        return self.__project
