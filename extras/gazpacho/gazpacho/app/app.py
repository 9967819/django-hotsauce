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

import os
import urllib.request, urllib.parse, urllib.error
import urllib.parse

import gtk
import gobject
from kiwi.component import get_utility
from kiwi.environ import environ
from kiwi.ui.dialogs import BaseDialog, open, save, error, messagedialog
from kiwi.utils import gsignal, type_register

from gazpacho import __version__
from gazpacho import gapi
from gazpacho.actioneditor import GActionsView
from gazpacho.app.bars import bar_manager
from gazpacho.app.dialogs import SingleCloseConfirmationDialog, \
     MultipleCloseConfirmationDialog, UnsupportedWidgetsDialog
from gazpacho.app.preferences import PreferencesDialog
from gazpacho.app.uimstate import WidgetUIMState, ActionUIMState, \
     SizeGroupUIMState
from gazpacho.clipboard import clipboard, ClipboardWindow
from gazpacho.command import AccessorCommand
from gazpacho.commandmanager import command_manager
from gazpacho.config import config
from gazpacho.i18n import _
from gazpacho.interfaces import IPluginManager
from gazpacho.loader.loader import ParseError, ObjectBuilder
from gazpacho.palette import palette
from gazpacho.placeholder import Placeholder
from gazpacho.project import Project
from gazpacho.propertyeditor import PropertyEditor
from gazpacho.sizegroupeditor import SizeGroupView
from gazpacho.stockicons import register_stock_icons
from gazpacho.gadget import Gadget
from gazpacho.widgetview import WidgetTreeView
from gazpacho.widgetregistry import widget_registry
from gazpacho.workspace import WorkSpace

__all__ = ['Application']

# The maximum number of recent items to display
MAX_RECENT_ITEMS = 5

class Application(gobject.GObject):
    """
    Application represents the Gazpacho application itself.

    Signals:
      set-project: a project is set as the current project. This usually
        happens when opening a project.
      close-project: a project is closed
    """
    gsignal('set-project', object),
    gsignal('close-project', object)

    # DND information
    TARGET_TYPE_URI = 100
    targets = [('text/uri-list', 0, TARGET_TYPE_URI)]

    def __init__(self):
        gobject.GObject.__init__(self)

        # The WidgetAdaptor that we are about to add to a container. None if no
        # class is to be added. This also has to be in sync with the depressed
        # button in the Palette
        self._add_class = None

        # This is our current project
        self._project = None
        self._project_counter = 1

        # Merge IDs
        self._recent_menu_uid = -1
        self._open_projects_uid = -1

        # The uim_states maps notebook page numbers to uim states
        self._uim_states = {}
        # The uim state that is currently active
        self._activ_uim_state = None

        # debugging windows
        self._command_stack_window = None
        self._clipboard_window = None

        # here we put views that should update when changing the project
        self._project_views = []

        self._active_view = None
        self._projects = []
        self._show_structure = False

        register_stock_icons()

        self._window = self._application_window_create()

        # Initialize the Plugin Manager
        plugin_manager = get_utility(IPluginManager)
        plugin_manager.load_plugins()
        plugin_manager.activate_plugins(config.get_plugins(), self)

    def _application_window_create(self):
        application_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        application_window.set_name('ApplicationWindow')
        application_window.connect('delete-event', self._delete_event_cb)
        iconfilename = environ.find_resource('pixmap', 'gazpacho-icon.png')
        gtk.window_set_default_icon_from_file(iconfilename)

        # Layout them on the window
        main_vbox = gtk.VBox()
        application_window.add(main_vbox)
        main_vbox.show()

        # Create actions that are always enabled
        bar_manager.add_actions(
            'Normal',
            # File menu
            ('FileMenu', None, _('_File')),
            ('New', gtk.STOCK_NEW, None, None,
             _('New Project'), self._new_cb),
            ('Open', gtk.STOCK_OPEN, None, None,
             _('Open Project'), self._open_cb),
            ('Quit', gtk.STOCK_QUIT, None, None,
             _('Quit'), self._quit_cb),

            # Edit menu
            ('EditMenu', None, _('_Edit')),
            ('Preferences', gtk.STOCK_PREFERENCES, None, None,
             _('Open the preferences dialog'), self._preferences_cb),

            # Object menu
            ('ObjectMenu', None, _('_Objects')),

            # Project menu
            ('ProjectMenu', None, _('_Project')),
            ('ProjectProperties', None, _('_Properties'), None,
             _('Project properties'), self._project_properties_cb),

            # (projects..)

            # Debug menu
            ('DebugMenu', None, _('_Debug')),
            ('DumpData', None, _('Dump data'), '<control>M',
              _('Dump debug data'), self._dump_data_cb),
            ('Preview', None, _('Preview'), None,
             _('Preview current window'), self._preview_cb),

            # Help menu
            ('HelpMenu', None, _('_Help')),
            ('About', gtk.STOCK_ABOUT, None, None, _('About Gazpacho'),
             self._about_cb),
            )

        # Toggle actions
        bar_manager.add_toggle_actions(
            'Normal',
            ('ShowStructure', None, _('Show _structure'), '<control><shift>t',
             _('Show container structure'), self._show_structure_cb, False),
            ('ShowCommandStack', None, _('Show _command stack'), 'F3',
             _('Show the command stack'), self._show_command_stack_cb, False),
            ('ShowClipboard', None, _('Show _clipboard'), 'F4',
             _('Show the clipboard'), self._show_clipboard_cb, False),
            ('ShowWorkspace', None, _('Show _workspace'), '<control><shift>t',
             _('Show container workspace'), self._show_workspace_cb, False),
            )

        # Create actions that reqiuire a project to be enabled
        bar_manager.add_actions(
            'ContextActions',
            # File menu
            ('Save', gtk.STOCK_SAVE, None, None,
             _('Save Project'), self._save_cb),
            ('SaveAs', gtk.STOCK_SAVE_AS, _('Save _As...'), '<shift><control>S',
             _('Save project with different name'), self._save_as_cb),
            ('Close', gtk.STOCK_CLOSE, None, None,
             _('Close Project'), self._close_cb),
            # Edit menu
            ('Undo', gtk.STOCK_UNDO, None, '<control>Z',
             _('Undo last action'), self._undo_cb),
            ('Redo', gtk.STOCK_REDO, None, '<shift><control>Z',
             _('Redo last action'), self._redo_cb)
            )

        bar_manager.add_actions(
            'AlwaysDisabled',
            # Edit menu
            ('Cut', gtk.STOCK_CUT, None, None,
             _('Cut'), None),
            ('Copy', gtk.STOCK_COPY, None, None,
             _('Copy'), None),
            ('Paste', gtk.STOCK_PASTE, None, None,
             _('Paste'), None),
            ('Delete', gtk.STOCK_DELETE, None, '<control>D',
             _('Delete'), None)
            )

        bar_manager.build_interfaces()
        self._update_recent_project_items()
        application_window.add_accel_group(bar_manager.get_accel_group())
        main_vbox.pack_start(bar_manager.get_menubar(), False)
        main_vbox.pack_start(bar_manager.get_toolbar(), False)

        hbox = gtk.HBox(spacing=6)
        main_vbox.pack_start(hbox)
        hbox.show()

        palette.connect('toggled', self._on_palette_toggled)
        hbox.pack_start(palette, False, False)
        palette.show_all()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_size_request(400, -1)
        hbox.pack_start(sw, True, True)

        self._workspace = WorkSpace()
        sw.add_with_viewport(self._workspace)
        self._workspace.show()
        self._workspace_sw = sw
        self._workspace_action = bar_manager.get_action(
            'ui/MainMenu/EditMenu/ShowWorkspace')

        vpaned = gtk.VPaned()
        vpaned.set_position(150)
        hbox.pack_start(vpaned, True, True)
        vpaned.show()

        notebook = gtk.Notebook()
        vpaned.add1(notebook)
        notebook.show()

        # Widget view
        widget_view = WidgetTreeView(self)
        self._add_view(widget_view)
        page_num = notebook.append_page(widget_view, gtk.Label(_('Widgets')))
        widget_view.show()

        state = WidgetUIMState()
        self._uim_states[page_num] = state

        # Action view
        self.gactions_view = GActionsView(self)
        self._add_view(self.gactions_view)
        page_num = notebook.append_page(self.gactions_view,
                                        gtk.Label(_('Actions')))
        self.gactions_view.show()

        state = ActionUIMState(self.gactions_view)
        self._uim_states[page_num] = state

        # Sizegroup view
        self.sizegroup_view = SizeGroupView(self)
        self._add_view(self.sizegroup_view)
        page_num = notebook.append_page(self.sizegroup_view,
                                        gtk.Label(_('Size Groups')))
        self.sizegroup_view.show()

        state = SizeGroupUIMState(self.sizegroup_view)
        self._uim_states[page_num] = state

        # Add property editor
        self._editor = PropertyEditor(self)
        vpaned.add2(self._editor)
        self._editor.show_all()

        notebook.connect('switch-page', self._on_notebook_switch_page)

        # Statusbar
        statusbar = gtk.Statusbar()
        self._statusbar_menu_context_id = statusbar.get_context_id("menu")
        self._statusbar_actions_context_id = statusbar.get_context_id("actions")
        main_vbox.pack_end(statusbar, False)
        self._statusbar = statusbar
        statusbar.show()

        # dnd doesn't seem to work with Konqueror, at least not when
        # gtk.DEST_DEFAULT_ALL or gtk.DEST_DEFAULT_MOTION is used. If
        # handling the drag-motion event it will work though, but it's
        # a bit tricky.
        application_window.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                                         Application.targets,
                                         gtk.gdk.ACTION_COPY)

        application_window.connect('drag-data-received',
                                   self._dnd_data_received_cb)

        # Enable the current state
        self._active_uim_state = self._uim_states[0]
        self._active_uim_state.enable()

        return application_window

    def _add_recent_project(self, project):
        """
        Add a project to the recent file list. This will also update
        the menu.

        @param project: the project to add
        @type project: L{gazpacho.project.Project}
        """
        if not project.path:
            return

        config.add_recent_project(project.path)
        self._update_recent_project_items()

    def _update_recent_project_items(self):
        """
        Update the list of recent projects in the menu.
        """
        if self._recent_menu_uid:
            bar_manager.remove_ui(self._recent_menu_uid)
            bar_manager.ensure_update()

        ui = ""
        for i, path in enumerate(config.recent_projects):
            if i == MAX_RECENT_ITEMS:
                break

            if not os.path.exists(path):
                config.recent_projects.remove(path)
                continue

            basename = os.path.basename(path)
            if basename.endswith('.glade'):
                basename = basename[:-6]

            ui += '<menuitem action="%s"/>' % basename
            label = '_%d. %s' % (i+ 1, basename)
            action = gtk.Action(basename, label, '', '')
            action.connect('activate', self._open_project_cb, path)
            bar_manager.add_action('RecentProjects', action)

        recent_template = '''<ui>
  <menubar name="MainMenu">
    <menu action="FileMenu">
      <placeholder name="RecentProjects">
      %s
      </placeholder>
    </menu>
  </menubar>
</ui>'''

        self._recent_menu_uid = bar_manager.add_ui_from_string(
            recent_template % ui)

    def _add_view(self, view):
        self._project_views.insert(0, view)
        view.set_project(self._project)
        view.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

    def _confirm_open_project(self, project):
        """
        Ask the user whether to reopen a project that has already been
        loaded (and thus reverting all changes) or just switch to the
        loaded version.

        @param project: the project we might reload
        @type project: L{gazpacho.project.Project}
        @return: True if the project should be reloaded
        @rtype: bool
        """
        submsg1 = _('"%s" is already open.') % project.name
        submsg2 = _('Do you wish to revert your changes and re-open the '
                    'glade file? Your changes will be permanently lost '
                    'if you choose to revert.')
        msg = '<span weight="bold" size="larger">%s</span>\n\n%s\n' % \
              (submsg1, submsg2)
        dialog = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE,
                                   msg)
        dialog.set_title('')
        dialog.label.set_use_markup(True)
        dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                           gtk.STOCK_REVERT_TO_SAVED, gtk.RESPONSE_YES)
        dialog.set_default_response(gtk.RESPONSE_CANCEL)

        result = dialog.run()
        dialog.destroy()
        return result == gtk.RESPONSE_YES

    def _add_project(self, project):
        # if the project was previously added, don't reload
        for prj in self._projects:
            if prj.path and prj.path == project.path:
                self._set_project(prj)
                return

        self._projects.insert(0, project)

        self._update_open_projects()

        # connect to the project signals so that the editor can be updated
        project.selection.connect_object('selection-changed',
                                         self._on_selection_changed,
                                         project)
        project.connect('changed', self._on_project_changed)
        project.connect('add-gadget', self._on_project_add_gadget)
        project.connect('remove-gadget', self._on_project_remove_gadget)
        project.undo_stack.connect('changed', self._on_undo_stack_changed)

        self._set_project(project)
        self._add_recent_project(project)

    def _update_open_projects(self):
        """
        Update the list of recent projects in the menu.
        """
        if self._open_projects_uid:
            bar_manager.remove_ui(self._open_projects_uid)

        ui = ""
        previous_action = None
        for project in self._projects:
            action = gtk.RadioAction(project.get_id(), project.name,
                                     project.name, '', hash(project))
            if previous_action:
                action.set_group(previous_action)
            action.connect('activate', self._set_project_cb, project)
            bar_manager.add_action('OpenProjects', action)

            ui += '<menuitem action="%s"/>' % action.get_name()
            previous_action = action

        open_projects_template = '''<ui>
  <menubar name="MainMenu">
    <menu action="ProjectMenu">
      <placeholder name="OpenProjects">
      %s
      </placeholder>
    </menu>
  </menubar>
</ui>'''

        self._open_projects_uid = bar_manager.add_ui_from_string(
            open_projects_template % ui)

        bar_manager.set_action_prop('ProjectProperties',
                                    sensitive=len(self._projects))
        bar_manager.ensure_update()

    def _set_project(self, project):
        """
        Set the specified project as the current project.

        @param project: the project
        @type project: gazpacho.project.Project
        """
        if project is self._project:
            return

        if project and project not in self._projects:
            print ('Could not set project because it could not be found '
                   'in the list')
            return

        self._project = project

        for view in self._project_views:
            view.set_project(project)

        for state in self._uim_states.values():
            state.set_project(project)

        self._refresh_title()
        self.refresh_command_stack_view()

        if project:
            # Make sure the radio action is set. This will trigger
            # another call to _set_project but since the project is
            # already set it will just be ignored
            action_name = ('/MainMenu/ProjectMenu/OpenProjects/%s'
                           % project.get_id())
            bar_manager.get_action(action_name).set_active(True)

            # trigger the selection changed signal to update the editor
            self._project.selection.selection_changed()

            # emit this signals so plugins can do their stuff
            self.emit('set-project', project)

        self._update_palette_sensitivity()

    def _refresh_title(self):
        if self._project:
            title = '%s - Gazpacho' % self._project.name
            if self._project.changed:
                title = '*' + title
        else:
            title = 'Gazpacho'
        self.set_title(title)

    def _refresh_project_entry(self, project):
        """Update the project label in the project menu."""
        bar_manager.set_action_prop(project.get_id(), label=project.name)

    def _is_writable(self, filename):
        """
        Check if it is possible to write to the file. If the file
        doesn't exist it checks if it is possible to create it.
        """
        if os.access(filename, os.W_OK):
            return True

        path = os.path.dirname(filename)
        if not os.path.exists(filename) and os.access(path, os.W_OK):
            return True

        return False

    def _save(self, project, path):
        """ Internal save """
        if self._is_writable(path):
            project.save(path)
            self._refresh_project_entry(project)
            self._refresh_title()
            success = True
        else:
            submsg1 = _('Could not save project "%s"') % project.name
            submsg2 = _('Project "%s" could not be saved to %s. '
                        'Permission denied.') % \
                        (project.name, os.path.abspath(path))
            text = '<span weight="bold" size="larger">%s</span>\n\n%s\n' % \
                   (submsg1, submsg2)
            result = messagedialog(
                gtk.MESSAGE_ERROR, text, parent=self._window,
                buttons=((gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
                         (gtk.STOCK_SAVE_AS, gtk.RESPONSE_YES)))

            if result == gtk.RESPONSE_YES:
                success = self._project_save_as(_('Save as'), project)
            else:
                success = False

        self._add_recent_project(project)
        return success

    def _project_save_as(self, title, project):
        filename = save(title, folder=config.lastdirectory)
        if not filename:
            return False

        config.set_lastdirectory(filename)

        return self._save(project, filename)

    def _close_project(self, project):
        """
        Close the project.

        @param project: the project to close
        @type project: L{gazpacho.project.Project}
        """
        project.selection.clear(False)
        if project is self._project:
            project.selection.selection_changed()

        for widget in project.get_widgets():
            widget.destroy()

        bar_manager.remove_ui(-1)
        self._projects.remove(project)

        self.emit('close-project', project)

    def _confirm_close_project(self, project):
        """Show a dialog asking the user whether or not to save the
        project before closing them.

        Return False if the user has chosen not to close the project.
        """
        return self._confirm_close_projects([project])

    def _confirm_close_projects(self, projects):
        """Show a dialog listing the projects and ask whether the user
        wants to save them before closing them.

        Return False if the user has chosen not to close the projects.
        """
        if not projects:
            return True

        if len(projects) == 1:
            dialog = SingleCloseConfirmationDialog(projects[0], self._window)
        else:
            dialog = MultipleCloseConfirmationDialog(projects, self._window)

        ret = dialog.run()
        if ret == gtk.RESPONSE_YES:
            # Go through the chosen projects and save them. Ask for a
            # file name if necessary.
            close = True
            projects_to_save = dialog.get_projects()
            for project in projects_to_save:
                if project.path:
                    saved = self._save(project, project.path)
                else:
                    title = _('Save as')
                    saved = self._project_save_as(title, project)
                    # If the user has pressed cancel we abort everything.
                if not saved:
                    close = False
                    break
        elif ret == gtk.RESPONSE_NO:
            # The user has chosen not to save any projects.
            close = True
        else:
            # The user has cancel the close request.
            close = False

        dialog.destroy()
        return close

    def _set_workspace_title(self, widget):
        self._workspace.set_widget_title(
            widget, '%s - %s' % (gobject.type_name(widget), widget.name))

    # debugging windows

    def _delete_event_for_debugging_window(self, window, event, action):
        # this will hide the window
        action.activate()
        # we don't want the window to be destroyed
        return True

    def _create_debugging_window(self, view, title, action):
        win = gtk.Window()
        win.set_title(title)
        win.set_transient_for(self._window)
        win.add(view)
        view.show_all()
        win.connect('delete-event',
                    self._delete_event_for_debugging_window, action)
        return win

    def _update_palette_sensitivity(self):
        """Update sensitivity of  UI elements (Palette) depending on
        the project list. If the list is empty we should unsensitive
        everything. Otherwise we should set sensitive to True.
        """
        if self._projects:
            palette.set_sensitive(True)
        else:
            palette.set_sensitive(False)


    # Public API

    def new_project(self):
        """
        Create and add a new project.
        """
        project = Project(self)
        project.name = _('Untitled %d') % self._project_counter
        self._project_counter += 1

        self._add_project(project)

    def get_current_project(self):
        """
        Get the currently selected project.

        @return: the project
        @rtype: L{gazpacho.project.Project}
        """
        return self._project

    def get_projects(self):
        """
        Get the open projects.

        @return: list of projects
        @rtype: list
        """
        return self._projects

    def open_project(self, path):
        """
        Open the project at the specified path. If the project has
        already been loaded we ask if we should reload it (close and
        reopen) or just switch to the loaded project.

        @param path: the path to the project file
        @type path: str
        """
        # Check if the project is loaded and ask the user what to do.
        for project in self._projects:
            if project.path and project.path == path:
                if not self._confirm_open_project(project):
                    self._set_project(project)
                    return project

                self._close_project(project)
                break

        project = Project(self)
        try:
            project.load(path)
        except ParseError:
            submsg1 = _('The project could not be loaded')
            submsg2 = _('An error occurred while parsing the file "%s".') % \
                      os.path.abspath(path)
            msg = '<span weight="bold" size="larger">%s</span>\n\n%s\n' % \
                      (submsg1, submsg2)
            error(msg)
            self._update_palette_sensitivity()
        except IOError:
            if path in config.recent_projects:
                config.recent_projects.remove(path)
                #self._update_recent_items()

            submsg1 = _('The project could not be loaded')
            submsg2 = _('The file "%s" could not be opened') % \
                      os.path.abspath(path)
            msg = '<span weight="bold" size="larger">%s</span>\n\n%s\n' % \
                      (submsg1, submsg2)
            error(msg)
            self._update_palette_sensitivity()

        failures = project.get_unsupported_widgets()
        if failures:
            dialog = UnsupportedWidgetsDialog(self._window, failures)
            dialog.run()
            dialog.destroy()

        self._add_project(project)
        return project

    def close_current_project(self):
        """
        Close the current project. If there still are open projects
        after the current project has been closed we select one of
        them.
        """
        if not self._project:
            return

        self._close_project(self._project)

        next_project = None
        if self._projects:
            next_project = self._projects[0]

        self._update_open_projects()
        self._set_project(next_project)

    def refresh_command_stack_view(self):
        # Update the command stack view
        if self._command_stack_window is not None:
            command_stack_view = self._command_stack_window.get_child()
            command_stack_view.update()

    def set_title(self, title):
        self._window.set_title(title)

    def refresh_editor(self, prop_name=None):
        self._editor.refresh(prop_name)

    def get_gadget_in_editor(self):
        return self._editor.get_loaded_gadget()

    def create(self, type_name):
        adaptor = widget_registry.get_by_name(type_name)
        gapi.create_gadget(self._project, adaptor, None)

    def run(self):
        """Display the window and run the application"""
        self._window.show()

        gtk.main()

    def validate_widget_names(self, project, show_error_dialogs=True):
        """Return True if all the widgets in project have valid names.

        A widget has a valid name if the name is not empty an unique.
        As soon as this function finds a widget with a non valid name it
        select it in the widget tree and returns False
        """

        widget_names = [widget.name for widget in project.get_widgets()]
        for widget in project.get_widgets():
            # skip internal children (they have None as the name)
            if widget.name is None:
                continue

            if widget.name == '':
                if show_error_dialogs:
                    error(_("There is a widget with an empty name"))
                project.selection.set(widget, True)
                return False

            widget_names.remove(widget.name)

            if widget.name in widget_names:
                if show_error_dialogs:
                    msg = _('The name "%s" is used in more than one widget')
                    error(msg % widget.name)
                project.selection.set(widget, True)
                return False

        return True

    def get_current_context(self):
        """Return the context associated with the current project or None if
        there is not such a project.
        """
        if self._project is None:
            return None
        return self._project.context

    # Properties

    def get_window(self):
        return self._window

    def get_add_class(self):
        return self._add_class
    add_class = property(get_add_class)

    # Callbacks

    def _on_palette_toggled(self, palette):
        """
        When a palette button is clicked one of two things can
        happen. If the button refers to a toplevel widget that widget
        is created and we are done. If it is not a toplevel widget we
        go into a mode where the widget will be added to the first
        placeholder that is selected.
        """
        adaptor = palette.current

        # adaptor may be None if the selector was pressed
        self._add_class = adaptor
        if adaptor and adaptor.is_toplevel():
            gapi.create_gadget(self._project, adaptor, None)

            palette.unselect_widget()
            self._add_class = None

    def _delete_event_cb(self, window, event):
        self._quit_cb()

        # stop other handlers
        return True

    def _on_notebook_switch_page(self, notebook, page, page_num):
        """
        Handler for the notebook's 'switch-page' signal. This will
        disable the current uim state, select a new and enable it
        instead.
        """
        # Disable old state
        self._active_uim_state.disable()

        # Select and enable new state
        state = self._uim_states[page_num]
        self._active_uim_state = state
        state.enable()

    def _on_undo_stack_changed(self, undo_stack):
        """
        Refresh the command stack view when the undo stack has
        changed.
        """
        self.refresh_command_stack_view()

    def _widget_notify_name_cb(self, widget, pspec):
        """
        The workspace title has to be updated when the widget name
        changes.
        """
        self._set_workspace_title(widget)

    def _on_project_add_gadget(self, project, gadget):
        """
        If a toplevel widget has been added it has to be added to the
        workspace as well.

        @param project: the project to which the gadget belongs
        @type project: L{gazpacho.project.Project}
        @param gadget: the gadget that has been added
        @type gadget: L{gazpacho.gadget.Gadget}
        """
        if not self._workspace_action.get_active():
            return

        if isinstance(gadget.widget, gtk.Window):
            gadget.widget.connect('notify::name', self._widget_notify_name_cb)
            self._workspace.add(gadget.widget)
            self._set_workspace_title(gadget.widget)

    def _on_project_remove_gadget(self, project, gadget):
        """
        If a toplevel widget has been removed from the project it has
        to be removed from the workspace as well.

        @param project: the project to which the gadget belongs
        @type project: L{gazpacho.project.Project}
        @param gadget: the gadget that has been removed
        @type gadget: L{gazpacho.gadget.Gadget}
        """
        if not self._workspace_action.get_active():
            return

        if isinstance(gadget.widget, gtk.Window):
            self._workspace.remove(gadget.widget)

    def _on_project_changed(self, project):
        """
        Refresh the title window title. This is done is done to show
        if the project has been modified since it was last saved.

        @param project: the project that has been modified
        @type project: L{gazpacho.project.Project}
        """
        self._refresh_title()

    def _on_selection_changed(self, project):
        """
        The widget selection has changed, switch to the project for
        which the selection belong and update the property editor.
        """
        # Set the sensitivity of the preview menu item
        bar_manager.set_action_prop('Preview',
                                    sensitive=(len(project.selection) == 1))

        # Decide if we have to switch to another project
        if self._project != project:
            self._set_project(project)
            return

        if self._editor:
            children = self._project.selection
            if len(children) == 1 and not isinstance(children[0], Placeholder):
                self._editor.display(Gadget.from_widget(children[0]))
            else:
                self._editor.hide_content()

    def _set_project_cb(self, action, project):
        """
        Set the correct project when the project menu item is
        selected.

        @param action: the action that triggered the event
        @type action: gtk.RadioAction
        @param project: the selected project
        @type project: L{gazpacho.project.Project}
        """
        # ignore the project that has been deselected
        if action.get_active():
            self._set_project(project)

    def _open_project_cb(self, action, path):
        self.open_project(path)

    def _create_command_view(self):
        from gazpacho.commandview import CommandView
        view = CommandView()
        self._add_view(view)

        title = _('Command Stack')
        action = bar_manager.get_action(
            '/MainMenu/DebugMenu/ShowCommandStack')
        self._command_stack_window = self._create_debugging_window(view,
                                                                   title,
                                                                   action)

    def _show_command_stack_cb(self, action):
        if self._command_stack_window is None:
            self._create_command_view()
            self._command_stack_window.show()
        else:
            if self._command_stack_window.get_property('visible'):
                self._command_stack_window.hide()
            else:
                self._command_stack_window.show_all()

    def _show_clipboard_cb(self, action):
        """Show/hide the clipboard window."""
        if self._clipboard_window is None:
            action = bar_manager.get_action(
                '/MainMenu/DebugMenu/ShowClipboard')
            self._clipboard_window = ClipboardWindow(self._window, clipboard)
            self._clipboard_window.connect(
                'delete-event', self._delete_event_for_debugging_window,
                action)
            self._clipboard_window.show_window()
        else:
            if self._clipboard_window.get_property('visible'):
                self._clipboard_window.hide_window()
            else:
                self._clipboard_window.show_window()

    def _dnd_data_received_cb(self, widget, context, x, y, data, info, time):
        """Callback that handles drag 'n' drop of glade files."""
        if info != Application.TARGET_TYPE_URI:
            return

        for uri in data.data.split('\r\n'):
            uri_parts = urllib.parse.urlparse(uri)
            if uri_parts[0] == 'file':
                path = urllib.request.url2pathname(uri_parts[2])
                self.open_project(path)

    # File action callbacks

    def _new_cb(self, action):
        self.new_project()

    def _open_cb(self, action):
        filename = open(parent=self._window, patterns=['*.glade'],
                        folder=config.lastdirectory)
        if filename:
            self.open_project(filename)
            config.set_lastdirectory(filename)

    def _save_cb(self, action):
        project = self._project

        # check that all the widgets have valid names
        if not self.validate_widget_names(project):
            return

        if project.path is not None:
            self._save(project, project.path)
            return

        # If instead we don't have a path yet, fire up a file chooser
        self._save_as_cb(None)

    def _save_as_cb(self, action):
        if action is None:
            # we were called from the _save_cb callback
            title = _('Save')
        else:
            title = _('Save as')
        self._project_save_as(title, self._project)

    def _close_cb(self, action):
        if not self._project:
            return

        if self._project.changed:
            close = self._confirm_close_project(self._project)
            if not close:
                return

        self.close_current_project()

    def _quit_cb(self, action=None):
        unsaved_projects = [p for p in self._projects if p.changed]
        close = self._confirm_close_projects(unsaved_projects)
        if not close:
            return

        config.save()

        plugin_manager = get_utility(IPluginManager)
        plugin_manager.deactivate_all()
        gtk.main_quit()

    # Edit action callbacks

    def _undo_cb(self, action):
        command_manager.undo(self._project)

    def _redo_cb(self, action):
        command_manager.redo(self._project)

    def _show_structure_cb(self, action):
        self._show_structure = not self._show_structure
        for project in self._projects:
            for widget in project.get_widgets():
                if isinstance(widget, gtk.Window):
                    widget.queue_draw()

    def _show_workspace_cb(self, action):
        workspace = self._workspace_sw
        if action.get_active():
            workspace.show()
        else:
            workspace.hide()

    def _preferences_cb(self, action):
        dialog = PreferencesDialog()
        dialog.run()

    # Project action callbacks

    def _project_properties_cb(self, action):
        # XXX: Use a glade file here, pending #329914 and #330652
        project = self.get_current_project()

        b = BaseDialog(self._window, _('Project properties'))
        b.set_resizable(False)
        b.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

        hbox = gtk.HBox(spacing=6)
        b.vbox.pack_start(hbox, False, False)
        hbox.show()

        label = gtk.Label()
        label.set_markup_with_mnemonic(_('_Translation domain:'))
        hbox.pack_start(label, False, False)
        label.show()

        entry = gtk.Entry()
        entry.connect('activate', lambda entry: b.response(gtk.RESPONSE_CLOSE))
        entry.set_text(project.get_domain())
        hbox.pack_start(entry, False, False)
        entry.show()
        b.vbox.show_all()

        response = b.run()
        if response == gtk.RESPONSE_CLOSE:
            domain = entry.get_text()
            if domain != project.get_domain():
                cmd = AccessorCommand(_('Set domain to %s') % domain,
                                      domain,
                                      project.set_domain,
                                      project.get_domain)
                command_manager.execute(cmd, project)
        b.destroy()

    # Debug action callbacks

    def _dump_data_cb(self, action):
        """This method is only useful for debugging.

        Any developer can print whatever he/she wants here
        the only rule is: clean everything before you commit it.

        This will be called upon CONTROL+M or by using the menu
        item Debug/Dump Data
        """
        project = self.get_current_project()
        print(project.serialize()[:-1])

        def dump_widget(widget, lvl=0):
            print('%s %s (%s)' % (' ' * lvl,
                                  gobject.type_name(widget),
                                  widget.get_name()))
            if isinstance(widget, gtk.Container):
                for child in widget.get_children():
                    dump_widget(child, lvl+1)

        for widget in project.get_widgets():
            if widget.get_parent():
                continue
            dump_widget(widget)

    def _preview_cb(self, action):
        project = self.get_current_project()
        if not project.selection:
            return

        xml = project.serialize()
        builder = ObjectBuilder(buffer=xml)
        toplevel = project.selection[0].get_toplevel()
        widget = builder.get_widget(toplevel.get_name())
        widget.show_all()

    # Help action callbacks

    def _about_cb(self, action):
        about = gtk.AboutDialog()
        about.set_name('Gazpacho')
        about.set_version(__version__)
        authorsfile = file(environ.find_resource('doc', 'AUTHORS'))
        authors = [a.strip() for a in authorsfile.readlines()]
        authors.append('') # separate authors from contributors
        contributorsfile = file(environ.find_resource('doc', 'CONTRIBUTORS'))
        authors.extend([c.strip() for c in contributorsfile.readlines()[:-2]])
        about.set_authors(authors)
        license = file(environ.find_resource('doc', 'COPYING')).read()
        about.set_license(license)
        about.set_website('http://gazpacho.sicem.biz')
        about.run()
        about.destroy()

    # Do not add anything here, add it above in the appropriate section

type_register(Application)
