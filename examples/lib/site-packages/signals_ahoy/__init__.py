# Django Signals Ahoy
# Copyright Bruce Kroeze 2009
#
# Released under the "New BSD License"
# Please see LICENSE.rst in this distribution for license details.
# -----------------

VERSION = (0, 1, 1)

# Dynamically calculate the version based on VERSION tuple
if len(VERSION)>2 and VERSION[2] is not None:
    str_version = "%d.%d_%s" % VERSION[:3]
else:
    str_version = "%d.%d" % VERSION[:2]

__version__ = str_version