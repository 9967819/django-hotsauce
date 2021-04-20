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

import gazpacho.widgets.base

# The root library is the name of the library Gazpacho will import to create
# the widgets. e.g import gtk
root_library = 'gtk'

# When loading the widget class from the catalog files we strip off this prefix
# for every widget
widget_prefix = 'Gtk'

# Silence pyflakes
gazpacho
