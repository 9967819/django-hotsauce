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

import os
import sys
from configparser import ConfigParser

MAX_RECENT = 10

"""[General]
lastdirectory=..
bugname=
bugmail=

[RecentProjects]
project0=..
project1=..

# in the plugins section each key represents a plugin
# and if the value is True that means the plugin should
# be activated when Gazpacho starts up
[Plugins]
foo=True
bar=True
"""

class ConfigError(Exception):
    pass

class BaseConfig:
    def __init__(self, filename):
        self._filename = filename
        self._config = ConfigParser()
        self.open(self._filename)

    def open(self, filename):
        if os.path.exists(filename):
            self._config.read(filename)
        self._filename = filename

    def has_option(self, name, section='General'):
        return self._config.has_option(section, name)

    def get_option(self, name, section='General'):
        if not section in self.sections:
            raise ConfigError('Invalid section: %s' % section)

        if self._config.has_option(section, name):
            return self._config.get(section, name)

        raise ConfigError('%s does not have option: %s' %
                          (self._filename, name))

    def set_option(self, name, value, section='General'):
        if not section in self.sections:
            raise ConfigError('Invalid section: %s' % section)

        if not self._config.has_section(section):
            self._config.add_section(section)

        self._config.set(section, name, value)

    def save(self):
        filename = self._filename
        fp = open(filename, 'w')
        self._config.write(fp)

def get_app_data_dir(appname):
    if sys.platform == 'win32':
        try:
            # C:\Documents and Settings\<user>\Application Data
            from win32com.shell.shell import SHGetFolderPath
            try:
                from win32com.shellcon import CSIDL_APPDATA
                folder_type = CSIDL_APPDATA
            except ImportError:
                folder_type = 0x001a
            app_data_dir = SHGetFolderPath(0, folder_type, 0, 0)
        except ImportError:
            # default to C:\
            app_data_dir = 'C:\\'
        return os.path.join(app_data_dir, appname)
    else:
        return os.path.join(os.path.expanduser('~'), '.' + appname)

class GazpachoConfig(BaseConfig):
    sections = ['General', 'RecentProjects', 'Plugins']
    def __init__(self):
        self.recent_projects = []
        self.lastdirectory = None
        self.plugins = []
        BaseConfig.__init__(self, self.get_filename())

    def get_filename(self):
        projectdir = get_app_data_dir('gazpacho')
        if not os.path.exists(projectdir):
            os.mkdir(projectdir)
        return os.path.join(projectdir, 'config')

    def open(self, filename):
        BaseConfig.open(self, filename)

        if self.has_option('lastdirectory'):
            self.lastdirectory = self.get_option('lastdirectory')

        i = 0
        while True:
            name = 'project%d' % i
            if not self.has_option(name, 'RecentProjects'):
                break

            self.recent_projects.append(self.get_option(name, 'RecentProjects'))
            i += 1

    def save(self):
        self.set_option('lastdirectory', self.lastdirectory)
        for i, project in enumerate(self.recent_projects):
            self.set_option('project%d' % i, project, 'RecentProjects')

        BaseConfig.save(self)

    def set_lastdirectory(self, filename):
        if not os.path.isdir(filename):
            filename = os.path.dirname(filename)
        self.lastdirectory = filename

    def add_recent_project(self, path):
        """
        Add a project to the recent project list.

        @param path: the project path
        @type path: str
        """
        if not path:
            return

        if path in self.recent_projects:
            self.recent_projects.remove(path)
            self.recent_projects.insert(0, path)
            return

        self.recent_projects.insert(0, path)
        if len(self.recent_projects) > MAX_RECENT:
            self.recent_projects = self.recent_projects[:MAX_RECENT]

    def set_bugname(self, name):
        self.set_option('bugname', name)

    def get_bugname(self):
        if self.has_option('bugname'):
            return self.get_option('bugname')
        return ''

    def set_bugmail(self, name):
        self.set_option('bugmail', name)

    def get_bugmail(self):
        if self.has_option('bugmail'):
            return self.get_option('bugmail')
        return ''

    def set_plugin(self, plugin, activated):
        if not self._config.has_section('Plugins'):
            self._config.add_section('Plugins')

        self.set_option(plugin, activated, 'Plugins')

    def get_plugins(self):
        plugins = []
        if self._config.has_section('Plugins'):
            section = self._config.items('Plugins')
            plugins = [name for name, value in section
                                if self._config.getboolean('Plugins', name)]
        return plugins

config = GazpachoConfig()
