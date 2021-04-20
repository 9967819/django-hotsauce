# Copyright (C) 2006 Mattias Karlsson
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

class SignalHandlerStorage:
    """
    The signal storage is used to keep track of signal handlers and
    provides a way to disconnect all of them in an simple way.
    """

    def __init__(self):
        """
        Initialize the signal storage.
        """
        self._handlers = {}

    def connect(self, obj, signal, callback, *args):
        """
        Connect a signal handler. All handlers connected in this way
        can be disconnected by calling disconnet().

        @param obj: the object to connect the handler to
        @type obj: gobject.GObject
        @param signal: the signal to listen for
        @type signal: str
        @param callback: the callback method
        @type callback: function object
        """
        handler_id = obj.connect(signal, callback, *args)
        self._handlers.setdefault(obj, []).append(handler_id)

    def disconnect_all(self):
        """
        Disconnect all handlers.
        """
        for obj, handler_ids in self._handlers.items():
            for hid in handler_ids:
                obj.disconnect(hid)

        self._handlers = {}
