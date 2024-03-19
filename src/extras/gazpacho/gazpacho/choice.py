# Copyright (C) 2004,2005 by SICEm S.L.
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

def enum_to_string(enum_value, pspec=None, enum=None):
    if pspec:
        enum_class = pspec.enum_class
    elif enum:
        enum_class = enum
    else:
        raise AssertionError

    if enum_class is not None:
        for value, enum in list(enum_class.__enum_values__.items()):
            if value == enum_value:
                return enum.value_nick
    return ""

def flags_to_string(flags_value, pspec=None, flags=None):
    """Convert a flag value (integer) to a string, using the pspec
    for introspection.
    It tries fairly hard to return a string as short as possible"""

    def isflag(n):
        """Helper to find the number of 1 in an integer.
        We're only interested in numbers with exactly one 1.
        """

        ones = 0
        i = 0
        while 1:
            # The value is too large, skip out
            if (1 << i) > n:
                break

            # Check if the ith bit of n is set
            if (n >> i) & 1 == 1:
                ones += 1

            if ones > 1:
                return False

            i += 1

        return ones == 1

    if flags_value == 0:
        return ""

    if pspec:
        flags_class = pspec.flags_class
    elif flags:
        flags_class = flags
    else:
        raise AssertionError

    flags_names = []
    for value, flag in list(flags_class.__flags_values__.items()):
        if not isflag(value):
            continue

        if (value & flags_value) == 0:
            continue

        for nick in flag.value_nicks:
            if nick in flags_names:
                continue

            flags_names.append(nick)

    flags_names.sort()
    retval = ' | '.join(flags_names)
    return retval
