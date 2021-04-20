# Copyright (C) 2004,2005 by SICEm S.L., Imendio AB and Async Open Source
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

import os
import sys
import warnings
import xml.dom.minidom
from xml.sax.saxutils import unescape

from kiwi.ui import dialogs
from kiwi.environ import environ

from gazpacho.config import get_app_data_dir
from gazpacho.library import load_library, LibraryLoadError
from gazpacho.loader.custom import valuefromstringsimpletypes, \
                                    get_pspec_from_name, str2bool
from gazpacho.properties import prop_registry
from gazpacho.widgetregistry import widget_registry

def xml_get_text_from_node(xmlnode):
    text = ''
    for node in xmlnode.childNodes:
        if node.nodeType == node.TEXT_NODE:
            text += node.data
    return unescape(text)

class BadCatalogSyntax(Exception):
    def __init__(self, file, msg):
        Exception.__init__(self, msg)
        self.file, self.msg = file, msg

    def __str__(self):
        return "Bad syntax in the catalog %s: %s" % (self.file, self.msg)

class CatalogError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class WidgetGroup(list):
    """List class used to store a widget group and its child nodes.

    The name property sets/gets the group internal name.
    The title property sets/gets the group title string.
    The class list contains the widget type strings for the group.
    """
    def __init__(self, name, title):
        list.__init__(self)
        self.name = name
        self.title = title

class Catalog:
    """Class to hold widget classes and groups.

    The title property gets/sets the catalog title string.
    The library property gets/sets the catalog library string.
    The widget_groups attribute holds a list of widget groups in the catalog.
    """
    def __init__(self, filename, resources_path):
        self.title = None
        self.library = None
        self.resource_path = resources_path
        self.widget_groups = []
        self.filename = filename
        self._parse_filename(filename)

    def _parse_filename(self, filename):
        fp = file(environ.find_resource('catalog', filename))
        document = xml.dom.minidom.parse(fp)
        root = document.documentElement
        self._parse_root(root)

    def _parse_root(self, node):
        # <!ELEMENT glade-catalog (glade-widget-classes?,
        #                          glade-widget-group*)>

        if node.nodeName == 'glade-catalog':
            self._parse_catalog(node)
        else:
            msg = "Root node is not glade catalog: %s" % node.nodeName
            raise BadCatalogSyntax(self.filename, msg)

        for child in node.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue

            if child.nodeName == 'glade-widget-classes':
                self._parse_widget_classes(child)
            elif child.nodeName == 'glade-widget-group':
                self._parse_widget_group(child)
            else:
                print('Unknown node: %s' % child.nodeName)

    def _parse_catalog(self, node):
        # <!ELEMENT glade-catalog (glade-widget-classes?,
        #                          glade-widget-group*)>
        # <!ATTLIST glade-catalog name            CDATA #REQUIRED
        #                         priority        CDATA #IMPLIED
        #                         library         CDATA #IMPLIED
        #                         library-type  (c|python) #IMPLIED
        #                         requires        CDATA #IMPLIED>

        # name
        self.title = str(node.getAttribute('name'))

        # priority
        priority = sys.maxsize
        if node.hasAttribute('priority'):
            priority = int(node.getAttribute('priority'))
        self.priority = priority

        # library
        library_name = str(node.getAttribute('library'))

        # library-type
        library_type = "python"
        if node.hasAttribute('library-type'):
            library_type = str(node.getAttribute('library-type'))

        name = os.path.basename(self.filename[:-4])
        try:
            self.library = load_library(library_type, name, library_name)
        except LibraryLoadError as e:
            raise CatalogError('Could not load library %s: %s' % (
                name, e))

    def _parse_widget_classes(self, node):
        "<!ELEMENT glade-widget-classes (glade-widget-class+)>"

        for class_node in node.childNodes:
            if class_node.nodeName != 'glade-widget-class':
                continue

            self._parse_widget_class(class_node)

    def _parse_widget_class(self, node):
        # <!ELEMENT glade-widget-class (tooltip?)>
        # <!ATTLIST glade-widget-class name          CDATA #REQUIRED
        #                              generic-name  CDATA #IMPLIED
	#	                       title         CDATA #IMPLIED
        #                              adaptor-class CDATA #IMPLIED>
        #                              register-type-function CDATA #IMPLIED>

        name = str(node.getAttribute('name'))
        if widget_registry.has_name(name):
            raise CatalogError("WidgetAdaptor %s is already registered" % name)

        generic_name = str(node.getAttribute('generic-name'))
        palette_name = str(node.getAttribute('title'))
        adaptor_class_name = str(node.getAttribute('adaptor-class'))

        tooltip = None
        for child in node.childNodes:
            if child.nodeName == 'tooltip':
                tooltip = xml_get_text_from_node(child)

        try:
            adaptor_class = self.library.get_widget_adaptor_class(
                name, adaptor_class_name)
        except LibraryLoadError as e:
            print('Could not load %s: %s' % (name, e))
            return

        adaptor = adaptor_class(name, generic_name, palette_name, self.library,
                                self.resource_path, tooltip)

        # store the Widget Adaptor on the cache
        widget_registry.add(adaptor)

    def _parse_widget_group(self, node):
        # <!ELEMENT glade-widget-group (glade-widget-class-ref+)>
        #  <!ATTLIST glade-widget-group name  CDATA #REQUIRED
        #                               title CDATA #REQUIRED>

        name = str(node.getAttribute('name'))
        title = str(node.getAttribute('title'))

        widget_group = WidgetGroup(name, title)

        for child in node.childNodes:
            if child.nodeName != 'glade-widget-class-ref':
                continue

            name = str(child.getAttribute('name'))
            widget_adaptor = widget_registry.get_by_name(name)
            if widget_adaptor is not None:
                widget_group.append(widget_adaptor)
            else:
                print('Could not load widget class %s' % name)

        self.widget_groups.append(widget_group)

    def __repr__(self):
        return '<Catalog %s>' % self.title

def _parse_gazpacho_path():
    """
    Parses the environment variable GAZPACHO_PATH and
    process all the directories in there
    """

    import gazpacho.widgets

    for path in os.environ.get('GAZPACHO_PATH', '').split(os.pathsep):
        if not path:
            continue

        environ.add_resource('pixmap', os.path.join(path, 'resources'))
        environ.add_resource('catalog', path)
        environ.add_resource('resource', os.path.join(path, 'resources'))
        environ.add_resource('glade', path)

        # library uses gazpacho.widgets as a base for plugins,
        # attach ourselves to it's __path__ so imports will work
        gazpacho.widgets.__path__.append(path)

def _get_catalog_dirs():
    catalog_error = ""

    _parse_gazpacho_path()
    catalogs = []
    for dirname in environ.get_resource_paths('catalog'):
        try:
            dir_list = os.listdir(dirname)
        except OSError as e:
            if e.errno == 2:
                catalog_error = ("The catalog directory %s does not exist" %
                                 dirname)
            elif e.errno == 13:
                catalog_error = ("You do not have read permissions in the "
                                 "catalog directory %s" % dirname)
            else:
                catalog_error = e.strerror

        if catalog_error:
            raise EnvironmentError(catalog_error)

        for filename in dir_list:
            if not filename.endswith('.xml'):
                continue
            name = filename[:-4]
            item = name, os.path.join(dirname, filename)
            # Make sure the base catalog is always loaded first, see #343283
            # We should introduce proper dependencies in the future.
            if name == 'base':
                catalogs.insert(0, item)
            else:
                catalogs.append(item)

    for name, filename in catalogs:
        if name == 'base':
            break
    else:
        raise SystemExit("Unable to find GTK+ catalog which is mandatory")

    return catalogs

_catalogs = []

def get_all_catalogs():
    """Return a list of existing Catalogs.

    The application widget registry is cleared and previously loaded classes
    and groups removed before rereading existing catalogs.
    The GTK+ catalog takes precedence and catalogs are ordered after
    their declared priority.
    """
    global _catalogs

    if not _catalogs:
        load_catalogs()

    assert _catalogs
    return _catalogs

def load_catalogs(external=True):
    """
    @param external: If true, allow loading of external (eg, not base) catalogs
    """
    try:
        catalogs = _get_catalog_dirs()
    except EnvironmentError as e:
        dialogs.error("<b>There were errors while loading Gazpacho</b>", str(e))
        raise SystemExit

    problems = []
    for name, filename in catalogs:
        # Skip external catalogs, for the testsuite.
        if not external and name != 'base':
            continue

        if filename.endswith('gtk+.xml'):
            warnings.warn("gtk+.xml found, it has been replaced by " +
                          "base.xml. Please remove it.", stacklevel=2)
            continue

        resources_path = environ.get_resource_paths('resource')
        try:
            catalog = Catalog(filename, resources_path)
            _catalogs.append(catalog)
        except IOError as e:
            problems.append(str(e))
        except BadCatalogSyntax as e:
            problems.append(str(e))
        except CatalogError as e:
            print('Error while loading catalog %s: %s' % (name, e))

    if problems:
        dialogs.error('\n'.join(problems))

    _catalogs.sort(lambda c1, c2: cmp(c1.priority,
                                      c2.priority))

# Default name of the file that contains custom UI definitions
CUSTOM_UI_FILENAME = 'custom.ui'

def get_custom_ui_filename():
    """Return the name of the file with custom UI definitions if it exists

    First it look in the user home directory (in the .gazpacho subdirectory),
    then it looks in every directory where there are catalogs.
    """
    # First we look in the user home directory
    app_dir = get_app_data_dir('gazpacho')
    custom_ui_filename = os.path.join(app_dir, CUSTOM_UI_FILENAME)
    if os.path.exists(custom_ui_filename):
        return custom_ui_filename

    # Then, look at standard catalog places
    for dirname in environ.get_resource_paths('catalog'):
        custom_ui_filename = os.path.join(dirname, CUSTOM_UI_FILENAME)
        if os.path.exists(custom_ui_filename):
            return custom_ui_filename

class CustomUI(object):
    """A Custom User Interface definition

    Using a XML file it is possible to redefine some parts of Gazpacho UI.
    Right now you can:

    - Change the palette grouping of widgets (you can mix widgets from
      different catalogs into the same palette groups)

    - Change the default value of a property of a widget

    - Hide a property making it non editable

    - Change the order of the properties in the editor by modifing its priority
    """

    def __init__(self, filename):
        """Constructor.

        It parses the file and changes the Gazpacho UI using its definitions
        """
        self.filename = filename
        self.widget_groups = []

        document = xml.dom.minidom.parse(file(filename))
        root = document.documentElement

        if root.nodeName != 'gazpacho-custom-ui':
            msg = "Root node is not gazpacho-custom-ui: %s" % root.nodeName
            raise BadCatalogSyntax(filename, msg)

        self._parse_root(root)

    def _parse_root(self, root):
        """Parser start point"""
        for child in root.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue

            if child.nodeName == 'palette-group':
                self._parse_custom_widget_group(child)
            else:
                print('Unknown node: %s' % child.nodeName)

    def _parse_custom_widget_group(self, node):
        """Parse a widget group and store it on a instance attribute"""
        name = str(node.getAttribute('name'))
        title = str(node.getAttribute('title'))

        widget_group = WidgetGroup(name, title)

        for child in node.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue

            if child.nodeName == 'widget':
                name = str(child.getAttribute('name'))
                widget_adaptor = widget_registry.get_by_name(name)
                if widget_adaptor is not None:
                    widget_group.append(widget_adaptor)
                    self._parse_custom_widget(name, child)
                else:
                    print('Could not load widget class %s' % name)

            else:
                print('Unknown node: %s' % child.nodeName)
        self.widget_groups.append(widget_group)

    def _parse_custom_widget(self, widget_name, node):
        """Parse a widget changing its property types"""
        for child in node.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue

            if child.nodeName == 'property':
                prop_name = str(child.getAttribute('name'))
                full_name = '%s::%s' % (widget_name, prop_name)
                attrs = {}
                for i in range(child.attributes.length):
                    attr = child.attributes.item(i)
                    name = str(attr.name)
                    value = attr.value
                    if name == 'name':
                        continue

                    if name == 'default':
                        value = _valuefromstring(widget_name, prop_name, value)

                    elif name in ('readable', 'writable', 'enabled',
                                  'translatable', 'editable'):
                        value = str2bool(value)

                    elif name == 'priority':
                        value = int(value)

                    else:
                        print('Customization of attribute %s is not supported' % name)
                        continue

                    attrs[str(attr.name)] = value

                if 'default' in list(attrs.keys()):
                    attrs['has_custom_default'] = True

                prop_registry.override_simple(full_name, **attrs)

            else:
                print('Unknown node: %s' % child.nodeName)

def _valuefromstring(widget_name, prop_name, string_value):
    """Helper function to convert a string to a valid value

    This is used when parsing default values for custom ui properties.
    """
    pspec = get_pspec_from_name(widget_name, prop_name)
    prop_type = pspec.value_type
    value = valuefromstringsimpletypes(prop_type, string_value)
    return value
