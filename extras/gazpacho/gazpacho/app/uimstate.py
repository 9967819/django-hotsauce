import gobject
import gtk

from gazpacho.app.bars import bar_manager
from gazpacho.clipboard import clipboard
from gazpacho.constants import STOCK_SIZEGROUP
from gazpacho.i18n import _
from gazpacho.placeholder import Placeholder
from gazpacho.sizegroupeditor import add_sizegroup_gadgets
from gazpacho.gadget import Gadget
from gazpacho.signalhandlers import SignalHandlerStorage

class UIMState(object):
    """
    The UIMState controls the state of the UIManager. It's responsible
    for enabling and disabling action as well as add and remove ui
    definitions.

    The UIMState is responsible for the basic functionallity such as
    Save, Close, Undo and Redo actions. It should be extended and
    customized to controll other actions as well.

    It is possible to have more than one UIMState but only one should
    be enabled at one time.
    """

    def __init__(self):
        """
        Initialize the uim state.
        """
        self._enabled = False
        self._project = None
        # Project dependent handlers
        self.handlers = SignalHandlerStorage()
        self._merge_ids = []
    #
    # Public methods
    #

    def enable(self):
        """
        Enable the state object.
        """
        self._enabled = True
        self.update_uim()
        self.update_state()

    def disable(self):
        """
        Disable the state object.
        """
        self._enabled = False
        self.update_uim()
        self.update_state()

    def set_project(self, project):
        """
        Set the current project.

        @param project: the new project
        @type project: L{gazpacho.project.Project}
        """
        # Disconnect handlers
        self.handlers.disconnect_all()
        self._project = project
        self.update_state()

        if not self._project:
            return

        # Connect handlers
        self.handlers.connect(project, 'changed',
                              self._on_project_changed)
        self.handlers.connect(project.undo_stack, 'changed',
                              self._on_undo_stack_changed)

    def update_state(self):
        """
        Make sure that the state of all actions are up to date.
        """
        group = bar_manager.get_group('ContextActions')
        group.set_sensitive(self._project is not None)

        if not self._enabled:
            return

        if not self._project:
            self._set_undo_redo_labels()
            return

        self._update_save_action(self._project)
        self._update_undo_redo_actions(self._project.undo_stack)

    def merge_ui(self, ui_string):
        """
        Merge a ui definition. It's currently only possibe to merge
        one ui definition, if you want to merge another you have to
        remove the first.

        @param ui_string: the ui definition
        @type ui_string: str
        """
        merge_id = bar_manager.add_ui_from_string(ui_string)
        self._merge_ids.append(merge_id)

    def remove_ui(self):
        """
        Remove ui that has previously been merged. If nothing has been
        merge nothing will happen.
        """
        for merge_id in self._merge_ids:
            bar_manager.remove_ui(merge_id)
        self._merge_ids = []

    #
    # Private methods
    #

    def update_uim(self):
        """
        Update the UIManager. This will add or remove ui definitions
        as well as action groups. Note that this isn't really part of
        the public API but should be overridden by the subclasses.
        """
        raise NotImplementedError(
            "This method has to be overridden by subclasses")

    def _update_undo_redo_actions(self, undo_stack):
        """
        Update the undo/redo actions.

        @param undo_stack: the undo/redo stack
        @type undo_stack: L{gazpacho.project.UndoRedoStack}
        """
        undo_info = redo_info = None
        if self._project:
            undo_info = undo_stack.get_undo_info()
            redo_info = undo_stack.get_redo_info()

        bar_manager.set_action_prop('Undo', sensitive=undo_info is not None)
        bar_manager.set_action_prop('Redo', sensitive=redo_info is not None)
        self._set_undo_redo_labels(undo_info, redo_info)

    def _set_undo_redo_labels(self, undo_text=None, redo_text=None):
        """
        Set the undo and redo labels. If no text has been specified a
        default label will be used to indicate that there are no undo
        or redo available.

        @param undo_text: the text that describes the undo action
        @type undo_text: str
        @param redo_text: the text that describes the redo action
        @type redo_text: str
        """
        if undo_text is None:
            undo_text = _('Nothing')

        if redo_text is None:
            redo_text = _('Nothing')

        bar_manager.set_action_prop('Undo',
                                    label=_('_Undo: %s') % undo_text,
                                    short_label=_('_Undo'))

        bar_manager.set_action_prop('Redo',
                                    label=_('_Redo: %s') % redo_text,
                                    short_label=_('_Redo'))

    def _update_save_action(self, project):
        """
        Update the save action.

        @param project: the current project
        @type project: L{gazpacho.project.Project}
        """
        bar_manager.set_action_prop('Save', sensitive=self._project.changed)

    #
    # Signal handlers
    #

    def _on_project_changed(self, project):
        """
        Callback for the project's changed signal that is emitted when
        the state of the project has changed.

        @param project: the project that has changed
        @type project: L{gazpacho.project.Project}
        """
        if self._enabled:
            self._update_save_action(project)

    def _on_undo_stack_changed(self, undo_stack):
        """
        Callback for the undo/redo stack's changed signal.

        @param undo_stack: the undo/redo stack
        @type undo_stack: L{gazpacho.project.UndoRedoStack}
        """
        if self._enabled:
            self._update_undo_redo_actions(undo_stack)


ACTION_UI_STRING = """
<ui>
  <menubar name="MainMenu">
    <menu action="ObjectMenu">
      <menuitem action="AddAction"/>
      <menuitem action="AddActionGroup"/>
      <menuitem action="EditAction"/>
    </menu>
  </menubar>
  <toolbar name="MainToolbar">
    <toolitem action="AddAction"/>
  </toolbar>
</ui>
"""

ACTION_POPUP_UI_STRING = """
<ui>
  <popup name="ActionPopup">
    <menuitem action="AddAction"/>
    <menuitem action="AddActionGroup"/>
    <menuitem action="EditAction"/>
    <menuitem action="Delete"/>
  </popup>
</ui>
"""

class ActionUIMState(UIMState):
    """
    The ActionUIMState is responsible for actions that has to do with
    the GActionView, i.e. adding, removing and editing actions and
    action groups.
    """

    def __init__(self, view):
        """
        Initialize the action uim state.

        @param view: the action view
        @type view: L{gazpacho.actioneditor.GActionsView}
        """
        UIMState.__init__(self)

        self._view = view
        self._action_group = self._create_action_group()

        # Connect handlers (the normal way)
        view.connect('selection-changed', self._on_view_selection_changed)

    #
    # Public methods
    #

    def update_state(self):
        """
        Make sure that the state of all actions are up to date.
        """
        UIMState.update_state(self)
        self._action_group.set_sensitive(self._project is not None)

        if not (self._project and self._enabled):
            return

        self._update_action_actions()

    #
    # Private  methods
    #

    def update_uim(self):
        """
        Update the UIManager. This will add or remove ui definitions
        as well as action groups.
        """
        if self._enabled:
            if not bar_manager.has_group(self._action_group.get_name()):
                bar_manager.add_action_group(self._action_group)
            self.merge_ui(ACTION_UI_STRING)
            self.merge_ui(ACTION_POPUP_UI_STRING)
        else:
            self.remove_ui()
            group_name = self._action_group.get_name()
            if bar_manager.has_group(group_name):
                bar_manager.remove_action_group(group_name)

    def _create_action_group(self):
        """
        Create an action group for the action and action group
        specific actions.

        @return: the action group
        @rtype: gtk.ActionGroup
        """
        group = gtk.ActionGroup('ActionActions')
        group.add_actions((('Delete', gtk.STOCK_DELETE, None, '<control>D',
                            _('Delete'), self._delete_cb),))

        action = gtk.Action('AddAction',
                            _('_Add Action...'),
                            _('Add an action'),
                            gtk.STOCK_ADD)
        action.connect('activate', self._add_action_cb)
        action.set_property('short-label', _('Action'))
        group.add_action(action)

        action = gtk.Action('AddActionGroup',
                            _('Add Action _Group...'),
                            _('Add an action group'),
                            gtk.STOCK_ADD)
        action.connect('activate', self._add_action_group_cb)
        action.set_property('short-label', _('Action Group'))
        group.add_action(action)

        action = gtk.Action('EditAction',
                            _('_Edit...'),
                            _('Edit selected action or action group'),
                            gtk.STOCK_EDIT)
        action.connect('activate', self._edit_action_cb)
        action.set_property('short-label', _('Edit'))
        group.add_action(action)

        return group

    def _update_action_actions(self):
        """
        Update the action and action group actions.
        """
        if not self._project:
            return

        bar_manager.set_action_prop('AddActionGroup', sensitive=True)

        if (self._view.get_selected_action() or
            self._view.get_selected_action_group()):
            sensitive = True
        else:
            sensitive = False

        bar_manager.set_action_props(('AddAction', 'Delete', 'EditAction'),
                                     sensitive=sensitive)

    #
    # Signal handlers
    #

    def _on_view_selection_changed(self, actionview, item):
        """
        Callback that is called when the selection in the action view
        has changed.

        @param actionview: the action view
        @type actionview: L{gazpacho.actioneditor.GActionsView}
        @param item: the selected gaction or gaction group
        @type item: L{gazpacho.gaction.GActionGroup} or
          L{gazpacho.gaction.GAction}
        """
        if self._enabled:
            self._update_action_actions()

    #
    # Action callbacks
    #

    def _delete_cb(self, action):
        gaction = self._view.get_selected_action()
        if gaction is not None:
            self._view.remove_action(gaction)

    def _add_action_cb(self, action):
        gaction = self._view.get_selected_action()
        self._view.add_action(gaction)

    def _add_action_group_cb(self, action):
        self._view.add_action_group()

    def _edit_action_cb(self, action):
        gaction = self._view.get_selected_action()
        if gaction is not None:
            self._view.edit_action(gaction)

    def _delete_action_cb(self, action):
        gaction = self._view.get_selected_action()
        if gaction is not None:
            self._view.remove_action(gaction)


SIZEGROUP_POPUP_UI_STRING = """
<ui>
  <popup name="SizeGroupPopup">
    <menuitem action="Delete"/>
  </popup>
</ui>
"""

class SizeGroupUIMState(UIMState):
    """
    The SizeGroupUIMState is responsible for actions that has to do
    with the SizeGroupView, i.e. manipulating sizegroups and their
    widgets.
    """

    def __init__(self, view):
        """
        Initialize the sizegroup uim state.

        @param view: the sizegroup view
        @type view: L{gazpacho.sizegroupeditor.SizeGroupView}
        """
        UIMState.__init__(self)

        self._view = view
        self._action_group = self._create_sizegroup_action_group()

        # Connect handlers (the normal way)
        view.connect('selection-changed', self._on_view_selection_changed)

    #
    # Public methods
    #

    def update_state(self):
        """
        Make sure that the state of all actions are up to date.
        """
        UIMState.update_state(self)
        self._action_group.set_sensitive(self._project is not None)

        if not (self._project and self._enabled):
            return

        enabled = self._view.has_selected()
        self._update_sizegroup_actions(enabled)

    #
    # Private  methods
    #

    def update_uim(self):
        """
        Update the UIManager. This will add or remove ui definitions
        as well as action groups.
        """
        if self._enabled:
            if not bar_manager.has_group(self._action_group.get_name()):
                bar_manager.add_action_group(self._action_group)
            self.merge_ui(SIZEGROUP_POPUP_UI_STRING)
        else:
            self.remove_ui()
            group_name = self._action_group.get_name()
            if bar_manager.has_group(group_name):
                bar_manager.remove_action_group(group_name)

    def _create_sizegroup_action_group(self):
        """
        Create an action group for the sizegroup specific actions.

        @return: the action group
        @rtype: gtk.ActionGroup
        """
        group = gtk.ActionGroup('Edit sizegroup actions')
        group.add_actions((('Delete', gtk.STOCK_DELETE, None, '<control>D',
                            _('Delete'), self._delete_cb),))
        return group

    def _update_sizegroup_actions(self, enabled):
        """
        Update the actions related to sizegroup manipulation.

        @param enabled: whether the actions should be enabled or not
        @type enabled: bool
        """
        bar_manager.set_action_prop('Delete', sensitive=enabled)

    #
    # Signal handlers
    #

    def _on_view_selection_changed(self, view, item):
        """
        Callback that is called when the selected item in the
        sizegroup view has changed.

        @param view: the sizegroup view
        @type view: L{gazpacho.sizegroupeditor.SizeGroupView}
        @param item: the selected widget or sizegroup
        @type item: L{gazpacho.sizegroup.GSizeGroup} or
          L{gazpacho.gadget.Gadget}
        """
        self._update_sizegroup_actions(bool(item))

    #
    # Action callbacks
    #

    def _delete_cb(self, action):
        self._view.remove_selected_item()


WIDGET_UI_STRING = """
<ui>
  <menubar name="MainMenu">
    <menu action="ObjectMenu">
      <menuitem action="AddSizeGroupWidgets"/>
    </menu>
  </menubar>
  <toolbar name="MainToolbar">
    <toolitem action="AddSizeGroupWidgets"/>
  </toolbar>
</ui>
"""

class WidgetUIMState(UIMState):
    """
    The WidgetUIMState is responsible for actions that has to do with
    widgets, i.e. adding, removing, cut and paste and so on.
    """

    def __init__(self):
        """
        Initialize the widget uim state.
        """
        UIMState.__init__(self)

        self._action_group = self._create_widget_action_group()

        # Connect handlers (the normal way)
        clipboard.connect('selection_changed',
                          self._on_clipboard_selection_changed)

    #
    # Public methods
    #

    def set_project(self, project):
        """
        Set the current project.

        @param project: the new project
        @type project: L{gazpacho.project.Project}
        """
        UIMState.set_project(self, project)

        if not project:
            return

        self.handlers.connect(project.selection, 'selection_changed',
                              self._on_project_selection_changed)

    def update_state(self):
        """
        Make sure that the state of all actions are up to date.
        """
        UIMState.update_state(self)
        self._action_group.set_sensitive(self._project is not None)

        if not (self._project and self._enabled):
            return

        selection = self._project.selection
        self._update_edit_actions(selection)
        self._update_sizegroup_actions(selection)

    #
    # Private  methods
    #

    def update_uim(self):
        """
        Update the UIManager. This will add or remove ui definitions
        as well as action groups.
        """
        if self._enabled:
            if not bar_manager.has_group(self._action_group.get_name()):
                bar_manager.add_action_group(self._action_group)
            self.merge_ui(WIDGET_UI_STRING)
        else:
            self.remove_ui()
            group_name = self._action_group.get_name()
            if bar_manager.has_group(group_name):
                bar_manager.remove_action_group(group_name)

    def _create_widget_action_group(self):
        """
        Create an action group for the widget specific actions.

        @return: the action group
        @rtype: gtk.ActionGroup
        """
        group = gtk.ActionGroup('WidgetActions')

        # We override the default cut, copy, paste and delete
        group.add_actions(
            (('Cut', gtk.STOCK_CUT, None, None, _('Cut'), self._cut_cb),
             ('Copy', gtk.STOCK_COPY, None, None, _('Copy'), self._copy_cb),
             ('Paste', gtk.STOCK_PASTE, None, None, _('Paste'),
              self._paste_cb),
             ('Delete', gtk.STOCK_DELETE, None, '<control>D', _('Delete'),
              self._delete_cb)
             )
            )

        action = gtk.Action('AddSizeGroupWidgets',
                            _('Add Size Group _Widgets'),
                            _('Add the selected widgets to a size group'),
                            STOCK_SIZEGROUP)
        action.connect('activate', self._add_sizegroup_gadgets_cb)
        action.set_property('short-label', _('Group'))
        group.add_action(action)

        return group

    def _update_paste_action(self, selection, clipboard_item):
        """
        Update the paste action.

        @param selection: the selected widgets
        @type selection: list
        @param clipboard_item: the selected item on the clipboard
        @type clipboard_item: L{gazpacho.clipboard.ClipboardItem}
        """
        sensitive = False
        if clipboard_item:
            # We can always paste a toplevel
            if clipboard_item.is_toplevel:
                sensitive = True

            # columns can be pasted in tree views
            elif (len(selection) == 1
                  and isinstance(selection[0], gtk.TreeView)
                  and gobject.type_is_a(clipboard_item.type,
                                        gtk.TreeViewColumn)):
                sensitive = True

            # otherwise we need a placeholder
            elif (len(selection) == 1
                  and isinstance(selection[0], Placeholder)):
                sensitive = True

        bar_manager.set_action_prop('Paste', sensitive=sensitive)


    def _update_edit_actions(self, selection):
        """
        Update the actions in the edit group.

        @param selection: the selected widgets
        @type selection: list
        """
        if len(selection) == 1:
            widget = selection[0]
            gadget = Gadget.from_widget(widget)

            # Placeholders cannot be cut or copied but sometimes deleted
            if isinstance(widget, Placeholder):
                bar_manager.set_action_props(('Copy', 'Cut'),
                                             sensitive=False)
                bar_manager.set_action_prop('Delete',
                                            sensitive=widget.is_deletable())

            # Internal children cannot be cut, copied or deleted.
            elif gadget.internal_name:
                bar_manager.set_action_props(('Copy', 'Cut', 'Delete'),
                                             sensitive=False)

            else:
                bar_manager.set_action_props(('Copy', 'Cut', 'Delete'),
                                             sensitive=True)
        else:
            bar_manager.set_action_props(('Copy', 'Cut', 'Delete'),
                                         sensitive=False)

        # Unless the widget is toplevel it can only be pasted on a placeholder
        item = clipboard.get_selected_item()
        self._update_paste_action(selection, item)


    def _update_sizegroup_actions(self, selection):
        """
        Update the sizegroup actions.

        @param selection: the selected widgets
        @type selection: list
        """
        sensitive = True

        if not selection:
            sensitive = False

        for widget in selection:
            if isinstance(widget, (gtk.Window, Placeholder)):
                sensitive = False

        bar_manager.set_action_prop('AddSizeGroupWidgets', sensitive=sensitive)

    #
    # Signal handlers
    #

    def _on_clipboard_selection_changed(self, clipboard, item):
        """
        Callback for the clipboard's selection-changed signal.

        @param clipboard: the clipboard
        @type clipboard: L{gazpacho.clipboard.Clipboard}
        @param item: the newly selected item
        @type item: L{gazpacho.clipboard.ClipboardItem}
        """
        if not self._enabled:
            return

        selection = self._project.selection
        self._update_paste_action(selection, item)

    def _on_project_selection_changed(self, project):
        """
        Callback for when the selected widget in this project has changed.

        @param project: the current project
        @type project: L{gazpacho.project.Project}
        """
        if not self._enabled:
            return

        selection = self._project.selection
        self._update_edit_actions(selection)
        self._update_sizegroup_actions(selection)

    #
    # Action callbacks
    #

    def _cut_cb(self, action):
        gadget = Gadget.from_widget(self._project.selection[0])
        clipboard.cut(gadget)

    def _copy_cb(self, action):
        gadget = Gadget.from_widget(self._project.selection[0])
        clipboard.copy(gadget)

    def _paste_cb(self, action):
        placeholder = None
        if len(self._project.selection) == 1:
            placeholder = self._project.selection[0]
        clipboard.paste(placeholder, self._project)

    def _delete_cb(self, action):
        self._project.delete_selection()

    def _add_sizegroup_gadgets_cb(self, action):
        """
        Callback that will add the selected widgets to a sizegroup
        specified by the user.

        @param action: the action that triggered the callback
        @type action: L{gtk.Action}
        """
        add_sizegroup_gadgets(self._project)
