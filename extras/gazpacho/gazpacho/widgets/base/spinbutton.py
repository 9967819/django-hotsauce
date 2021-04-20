# Copyright (C) 2005 by Async Open Source
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

from gazpacho.properties import prop_registry, CustomProperty, \
     ProxiedProperty, AdjustmentType, FloatType, IntType

class SpinAdjustmentType(AdjustmentType):
    def __init__(self, gobj):
        super(AdjustmentType, self).__init__(gobj)
        # Initialize us to the value fetch from the loader
        self._value = gobj.widget.get_adjustment()

prop_registry.override_simple('GtkSpinButton::adjustment', SpinAdjustmentType)

# Value is never saved, because it's already saved as the first item in the
# adjustment. Infact get_property in gtkspinbutton.c just returns
# spinbutton->adjustment->value, so it makes sense to ignore it.
class Value(CustomProperty):
    def save(self):
        pass
prop_registry.override_simple('GtkSpinButton::value', Value)

class AdjustmentProxy(ProxiedProperty):
    def get_target(self):
        return self.object.get_adjustment()

    def save(self):
        # Not saving, they're saved in GtkSpinButton::adjustment instead
        return

class Lower(AdjustmentProxy, FloatType):
    label = "Min"
    default = 0
    tooltip = "The minimum value the spinbutton can have"
    target_name = 'lower'
prop_registry.override_property('GtkSpinButton::lower', Lower)

class Upper(AdjustmentProxy, FloatType):
    label = "Max"
    default = 100
    tooltip = "The maximum value the spinbutton can have"
    target_name = 'upper'
prop_registry.override_property('GtkSpinButton::upper', Upper)

class Step(AdjustmentProxy, IntType):
    label = "Step increment"
    default = 1
    tooltip = "Increment applied for each left mousebutton press"
    target_name = 'step-increment'
prop_registry.override_property('GtkSpinButton::step-increment', Step)

class Page(AdjustmentProxy, IntType):
    label = "Page increment"
    default = 10
    tooltip = "Increment applied for each middle mousebutton press"
    target_name = 'page-increment'
prop_registry.override_property('GtkSpinButton::page-increment', Page)
