import gtk
import gobject
from kiwi.component import get_utility
from kiwi.environ import environ
from kiwi.ui.dialogs import BaseDialog, warning
from kiwi.utils import gsignal

from gazpacho.app.bars import bar_manager
from gazpacho.command import FlipFlopCommandMixin, Command
from gazpacho.commandmanager import command_manager
from gazpacho.i18n import _
from gazpacho.interfaces import IGazpachoApp
from gazpacho.sizegroup import GSizeGroup
from gazpacho.util import select_iter
from gazpacho.gadget import Gadget
from gazpacho.signalhandlers import SignalHandlerStorage
from gazpacho.sizegroup import safe_to_add_gadgets

EDITOR_OBJECT_COLUMN, EDITOR_CALLBACK_IDS_COLUMN = list(range(2))

class SizeGroupView(gtk.ScrolledWindow):
    """
    The sizegroup view/editor that displays the sizegroup tree.
    """

    gsignal('selection-changed', object)

    def __init__(self, app):
        """
        Initialize the size group editor.

        @param app: the application
        @type app: gazpacho.application.Application
        """
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_IN)

        self._app = app
        self.project = None
        self._handlers = SignalHandlerStorage()
        self._mode_icons = self._load_mode_icons()

        self._treeview = self._create_treeview()
        self._model = gtk.TreeStore(object, object)
        self._treeview.set_model(self._model)

        # Connect the callbacks
        self._treeview.connect('button-press-event',
                               self._on_treeview_button_press_event)
        self._treeview.connect('key-press-event',
                               self._on_treeview_key_press_event)
        selection = self._treeview.get_selection()
        selection.connect('changed', self._on_treeview_selection_changed)

        self.add(self._treeview)
        self._treeview.show()

    #
    # Private methods
    #

    def _create_treeview(self):
        """
        Create the TreeView.
        """
        treeview = gtk.TreeView()
        treeview.set_headers_visible(False)

        column = gtk.TreeViewColumn()

        renderer1 = gtk.CellRendererPixbuf()
        column.pack_start(renderer1, False)
        column.set_cell_data_func(renderer1, self._draw_cell_icon)

        renderer2 = gtk.CellRendererText()
        column.pack_start(renderer2)
        column.set_cell_data_func(renderer2, self._draw_cell_data)

        treeview.append_column(column)
        return treeview

    def _load_mode_icons(self):
        """
        Load the pixbufs that are to be used as sizegroup mode icons.

        Mode constants:
         - gtk.SIZE_GROUP_HORIZONTAL
         - gtk.SIZE_GROUP_VERTICAL
         - gtk.SIZE_GROUP_BOTH

        @return: a mapping of sizegroup mode constants to pixbufs
        @rtype: map
        """
        icon_names = {gtk.SIZE_GROUP_HORIZONTAL: 'sizegroup-horizontal.png',
                      gtk.SIZE_GROUP_VERTICAL: 'sizegroup-vertical.png',
                      gtk.SIZE_GROUP_BOTH: 'sizegroup-both.png'}
        icon_map = {}
        for key, name in icon_names.items():
            pixbuf = None
            filename = environ.find_resource('pixmap', name)
            if filename:
                pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
            icon_map[key] = pixbuf

        return icon_map

    def _draw_cell_icon(self, tree_column, cell, model, model_iter):
        """
        Draw the sizegroup or gadget icon.
        """
        row = model[model_iter]
        item = row[EDITOR_OBJECT_COLUMN]

        if isinstance(item, GSizeGroup):
            pixbuf = self._mode_icons.get(item.mode)
        else:
            pixbuf = item.adaptor.pixbuf

        cell.set_property('pixbuf', pixbuf)


    def _draw_cell_data(self, column, cell, model, model_iter):
        """
        Display the name of the sizegroup or widget
        """
        sizegroup = model[model_iter][EDITOR_OBJECT_COLUMN]
        text = sizegroup.name
        cell.set_property('text', text)


    def _populate_model(self):
        """
        Fill the view with data from the current project. This will
        add all sizegroups that belong to the project and also connect
        the necessary callbacks.

        Note, it is important that the project has been set befor
        calling this method.
        """
        sizegroup_iter = None
        for sizegroup in self.project.sizegroups:
            sizegroup_iter = self._add_sizegroup(sizegroup)

        if sizegroup_iter:
            select_iter(self._treeview, sizegroup_iter)

    def _add_sizegroup(self, sizegroup):
        """
        Add a sizegroup and its widgets to the treeview. This will the
        necessary callbacks as well.

        @param sizegroup: the sizegroup that should be added
        @type sizegroup: gazpacho.sizegroup.GSizeGroup

        @return: the iter pointing to the sizegroup that was added
        @rtype: gtk.TreeIter
        """
        id1 = sizegroup.connect('gadgets-added',
                                self._on_sizegroup_gadgets_added)
        id2 = sizegroup.connect('gadgets-removed',
                                self._on_sizegroup_gadgets_removed)
        id3 = sizegroup.connect('name-changed',
                                self._on_sizegroup_name_changed)

        sizegroup_iter = self._model.append(None, (sizegroup, (id1, id2, id3)))
        self._add_gadgets(sizegroup_iter, sizegroup.get_gadgets())
        return sizegroup_iter

    def _add_gadgets(self, sizegroup_iter, gadgets):
        """
        Add a number of gadgets to the treeview. This will the
        necessary callbacks as well.

        @param sizegroup_iter: the parent iter where the gadgets
          should be added
        @type sizegroup_iter: gtk.TreeIter
        @param gadgets: the gadgets that should be added
        @type gadgets: list (of gazpacho.gadget.Gadget)

        @return: the iter pointing to the last gadget that was added
        @rtype: gtk.TreeIter
        """
        sizegroup = self._model[sizegroup_iter][EDITOR_OBJECT_COLUMN]

        gadget_iter = None
        for gadget in gadgets:
            # FIXME: Disconnect callback
            gadget.widget.connect('notify::name',
                                  self._on_widget_notify_name,
                                  gadget,
                                  sizegroup)
            row = (gadget, ())
            gadget_iter = self._model.append(sizegroup_iter, row)

        return gadget_iter

    def _disconnect_item_callbacks(self, model_iter):
        """
        Disconnect all callbacks for the item (sizegroup or gadget)
        that the iter is pointing to.

        @param model_iter: the iter pointing to the item who's
                           callbacks should be disconnected
        @type model_iter: gtk.TreeIter
        """
        row = self._model[model_iter]
        item = row[EDITOR_OBJECT_COLUMN]
        ids = row[EDITOR_CALLBACK_IDS_COLUMN]
        for callback_id in ids:
            item.disconnect(callback_id)

    def _disconnect_all_callbacks(self, sizegroup_iter):
        """
        Disconnect all callbacks for a sizegroup and all its gadgets.

        @param sizegroup_iter: the iter pointing to the sizegroup
        who's callbacks should be disconnected
        @type sizegroup_iter: gtk.TreeIter
        """
        gadget_iter = self._model.iter_children(sizegroup_iter)
        while gadget_iter:
            self._disconnect_item_callbacks(gadget_iter)
            gadget_iter = self._model.iter_next(gadget_iter)

        self._disconnect_item_callbacks(sizegroup_iter)

    def _find_sizegroup(self, sizegroup):
        """
        Find a certain sizegroup in the TreeStore.

        @param sizegroup: the sizegroup that the gadget belong to
        @type sizegroup: gazpacho.sizegroup.GSizeGroup

        @return: the iter pointing to the sizegroup or None if it wasn't found
        @rtype: gtk.TreeIter
        """
        model = self._model
        for sizegroup_row in model:
            if sizegroup_row[EDITOR_OBJECT_COLUMN] == sizegroup:
                return sizegroup_row.iter
        return None

    def _find_gadget(self, sizegroup, gadget):
        """
        Find a certain gadget in the TreeStore.

        @param sizegroup: the sizegroup that the gadget belong to
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        @param gadget: the gadget that we're looking for
        @type gadget: gazpacho.gadget.Gadget

        @return: the iter pointing to the gadget or None if it wasn't found
        @rtype: gtk.TreeIter
        """
        sizegroup_iter = self._find_sizegroup(sizegroup)
        if not sizegroup_iter:
            return None

        model = self._model
        for gadget_row in model[sizegroup_iter].iterchildren():
            if gadget_row[EDITOR_OBJECT_COLUMN] == gadget:
                return gadget_row.iter
        return None

    #
    # Editor callbacks
    #

    def _on_treeview_selection_changed(self, selection):
        """
        Callback for selection changes in the tree view.

        @param selection: the selection that has changed
        @type selection: gtk.TreeSelection
        """
        model, model_iter = selection.get_selected()
        item = None
        if model_iter:
            item = model[model_iter][EDITOR_OBJECT_COLUMN]
        self.emit('selection-changed', item)

    def _on_treeview_key_press_event(self, view, event):
        """
        Callback for handling key press events. Right now it's only
        used for deleting sizegroups and gadgets.

        @param view: the sizegroup treeview
        @type view: gtk.TreeView
        @param event: the event that was triggered
        @type event: gtk.gdk.Event
        """
        if event.keyval in [gtk.keysyms.Delete, gtk.keysyms.KP_Delete]:
            bar_manager.activate_action('Delete')

    def _on_treeview_button_press_event(self, view, event):
        """
        Callback for handling mouse clicks. It is used to show a
        context menu.

        @param view: the sizegroup treeview
        @type view: gtk.TreeView
        @param event: the event that was triggered
        @type event: gtk.gdk.Event
        """
        if event.button != 3:
            return False

        # No need for a context menu if there is no project
        if not self.project:
            return False

        result = view.get_path_at_pos(int(event.x), int(event.y))
        if not result:
            return
        path = result[0]

        # Select the row
        view.set_cursor(path)
        view.grab_focus()

        # Show popup
        popup = bar_manager.get_widget('/SizeGroupPopup')
        popup.popup(None, None, None, event.button, event.time)
        return True

    #
    # General callbacks
    #

    def _on_project_add_sizegroup(self, project, sizegroup):
        """
        Callback that is executed when a sizegroup is added to a
        project.

        @param project: the project that the sizegroup was added to
        @type project: gazpacho.project.Project
        @param sizegroup: the sizegroup that have been added
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        """
        sizegroup_iter = self._add_sizegroup(sizegroup)
        if sizegroup_iter:
            select_iter(self._treeview, sizegroup_iter)

    def _on_project_remove_sizegroup(self, project, sizegroup):
        """
        Callback that is executed when a sizegroup is removed from a
        project.

        @param project: the project that the sizegroup was removed from
        @type project: gazpacho.project.Project
        @param sizegroup: the sizegroup that have been removed
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        """
        sizegroup_iter = self._find_sizegroup(sizegroup)
        if not sizegroup_iter:
            return

        self._disconnect_all_callbacks(sizegroup_iter)
        del self._model[sizegroup_iter]

    def _on_sizegroup_name_changed(self, sizegroup):
        """
        Callback that is executed when the name of a sizegroup has
        changed. This will make sure that the editor is updated.

        @param sizegroup: the sizegroup who's name has changed
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        """
        sizegroup_iter = self._find_sizegroup(sizegroup)
        if sizegroup_iter:
            path = self._model[sizegroup_iter].path
            self._model.row_changed(path, sizegroup_iter)


    def _on_sizegroup_gadgets_added(self, sizegroup, gadgets):
        """
        Callback that is executed when gadgets are added to a
        sizegroup. This will add the gadgets to the editor.

        @param sizegroup: the sizegroup that the gadgets belong to
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        @param gadgets: the gadgets that have been added
        @type gadgets: list (of gazpacho.gadget.Gadget)
        """
        sizegroup_iter = self._find_sizegroup(sizegroup)
        if not sizegroup_iter:
            return

        gadget_iter = self._add_gadgets(sizegroup_iter, gadgets)
        if gadget_iter:
            select_iter(self._treeview, gadget_iter)

    def _on_sizegroup_gadgets_removed(self, sizegroup, gadgets):
        """
        Callback that is executed when gadgets are removed from a
        sizegroup. This will remove the gadgets from the editor.

        @param sizegroup: the sizegroup that the gadgets belong to
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        @param gadgets: the gadgets that have been removed
        @type gadgets: list (of gazpacho.gadget.Gadget)
        """
        for gadget in gadgets:
            gadget_iter = self._find_gadget(sizegroup, gadget)
            if gadget_iter:
                self._disconnect_item_callbacks(gadget_iter)
                del self._model[gadget_iter]

    def _on_widget_notify_name(self, widget, pspec, gadget, sizegroup):
        """
        Callback that is executed when the name property of a gadget
        has changed. This will make sure that the editor is updated.

        @param widget: the widget who's name has changed
        @type widget: gtk.Widget
        @param pspec: the gobject.GParamSpec of the property that was changed
        @type pspec: gobject.GParamSpec
        @param sizegroup: the sizegroup that the gadgets belong to
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        """
        gadget_iter = self._find_gadget(sizegroup, gadget)
        if gadget_iter:
            path = self._model[gadget_iter].path
            self._model.row_changed(path, gadget_iter)

    #
    # Public methods
    #
    def has_selected(self):
        """
        Check if a sizegroup or gadget is selected in the tree.
        """
        model_iter = self._treeview.get_selection().get_selected()[1]
        return model_iter is not None

    def set_project(self, project):
        """
        Set the current project.

        @param project: the current project
        @type project: gazpacho.project.project
        """
        if self.project:
            for sizegroup_row in self._model:
                self._disconnect_all_callbacks(sizegroup_row.iter)
            self._handlers.disconnect_all()
            self._model.clear()

        self.project = project

        if not project:
            return

        self._populate_model()
        self._handlers.connect(project, 'add-sizegroup',
                               self._on_project_add_sizegroup)
        self._handlers.connect(project, 'remove-sizegroup',
                               self._on_project_remove_sizegroup)

    def remove_selected_item(self):
        """
        Convenient method for removing the selecte sizegroup or gadget

        This method will not remove the action group directly but
        delegate to the command manager.
        """
        model, model_iter = self._treeview.get_selection().get_selected()
        if not model_iter:
            return

        row = model[model_iter]
        if row.parent:
            sizegroup = row.parent[EDITOR_OBJECT_COLUMN]
            gadgets = [row[EDITOR_OBJECT_COLUMN]]
        else:
            sizegroup = row[EDITOR_OBJECT_COLUMN]
            gadgets = sizegroup.get_gadgets()

        cmd = CommandAddRemoveSizeGroupGadgets(sizegroup, gadgets, self.project,
                                               False)
        command_manager.execute(cmd, self.project)

gobject.type_register(SizeGroupView)

def add_sizegroup_gadgets(project, sizegroup=None, gadgets=[]):
    """
    Convenient method for adding gadgets to a sizegroup.

    If no sizegroup is specified, a dialog will prompt the user to choose one.

    If no gadgets are specified, the current project selected widgets will be
    added.

    @param project: the current project
    @type project: gazpacho.project.Project
    """
    if not project.selection:
        return

    if sizegroup is None:
        window = get_utility(IGazpachoApp).get_window()
        dialog = SizeGroupDialog(window, project.sizegroups)
        if dialog.run() != gtk.RESPONSE_OK:
            dialog.destroy()
            return

        sizegroup = dialog.get_selected_sizegroup()
        dialog.destroy()

    if not gadgets:
        gadgets = [Gadget.from_widget(w) for w in project.selection]

    add_gadgets = []
    for gadget in gadgets:
        # We don't add a gadget that's already in the sizegroup
        if not sizegroup.has_gadget(gadget):
            add_gadgets.append(gadget)

    if gadgets and not safe_to_add_gadgets(sizegroup, add_gadgets):
        warning(_("Cannot add the widget"),
                _("It's not possible to add a gadget who has an ancestor"
                  " or child in the sizegroup."))
        return

    cmd = CommandAddRemoveSizeGroupGadgets(sizegroup, add_gadgets, project,
                                           True)
    command_manager.execute(cmd, project)

DIALOG_MODE_NAME_COLUMN, DIALOG_MODE_VALUE_COLUMN = list(range(2))

DIALOG_SIZEGROUP_NAME_COLUMN, DIALOG_SIZEGROUP_COLUMN = list(range(2))

class SizeGroupDialog(BaseDialog):
    """
    A dialog for choosing which sizegroup the widgets should be added
    to. It also offers the possibility to create a new sizegroup.
    """

    def __init__(self, parent, sizegroups):
        """
        Initialize the dialog.

        @param sizegroups: all available sizegroups
        @type sizegroups: list (of gazpacho.sizegroup.GSizeGroup)
        """
        BaseDialog.__init__(self, title=_('Add Size Group Widgets'),
                            parent=parent)

        # Dict of available sizegroups
        self._sizegroups = self._get_sizegroup_dict(sizegroups)

        # Existing sizegroups combo
        self._sizegroup_combo = None

        # New sizegroup name
        self._name_entry = None

        # New sizegroup modes combo
        self._mode_combo = None

        # Radio buttons
        self._selection_radio = None
        self._new_radio = None

        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self._add_button = self.add_button(gtk.STOCK_ADD, gtk.RESPONSE_OK)

        self._create_content()

        # Set default name
        name = self._suggest_sizegroup_name()
        self._name_entry.set_text(name)

        self._name_entry.connect('changed', self._on_name_entry_changed)

        self.set_default_response(gtk.RESPONSE_OK)
        self.vbox.show_all()

    def _get_sizegroup_dict(self, sizegroups):
        """
        Get a dictionary that maps sizegroup names to sizegroups.

        @return: dict mapping name to sizegroup
        @rtype: dict (str: gazpacho.sizegroup.GSizeGroup)
        """
        group_dict = {}
        for sizegroup in sizegroups:
            group_dict[sizegroup.name] = sizegroup
        return group_dict

    #
    # Public methods
    #

    def get_selected_sizegroup(self):
        """
        Get the selected sizegroup. This might return an existing
        sizegroup or a new one.

        @return: the sizegroup
        @rtype: gazpacho.sizegroup.GSizeGroup
        """
        if self._selection_radio.get_active():
            model = self._sizegroup_combo.get_model()
            active = self._sizegroup_combo.get_active()
            sizegroup = model[active][DIALOG_SIZEGROUP_COLUMN]
        else:
            model = self._mode_combo.get_model()
            active = self._mode_combo.get_active()
            mode = model[active][DIALOG_MODE_VALUE_COLUMN]
            name =  self._name_entry.get_text()
            sizegroup = GSizeGroup(name, gtk.SizeGroup(mode))

        return sizegroup

    #
    # Private methods
    #

    def _create_content(self):
        """
        Create the dialog content.
        """
        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        # Existing sizegroup area
        self._selection_radio = gtk.RadioButton(None,
                                                _('Existing size group:'))
        self.vbox.pack_start(self._selection_radio, False, False)

        selection_area = self._create_sizegroup_selection_area(size_group)
        self.vbox.pack_start(selection_area, False, False)

        # New sizegroup area
        self._new_radio = gtk.RadioButton(self._selection_radio,
                                          _('New size group:'))
        self.vbox.pack_start(self._new_radio, False, False)

        new_sizegroup_area = self._create_new_sizegroup_area(size_group)
        self.vbox.pack_start(new_sizegroup_area, False, False)

        # Select which should be active
        if self._sizegroups:
            new_sizegroup_area.set_sensitive(False)
        else:
            self._selection_radio.set_sensitive(False)
            self._new_radio.set_active(True)
            selection_area.set_sensitive(False)

        # Add some handlers
        self._selection_radio.connect('toggled',
                                      self._on_radio_toggled, selection_area)
        self._new_radio.connect('toggled',
                                self._on_radio_toggled, new_sizegroup_area)


    def _create_sizegroup_selection_area(self, size_group):
        """
        Create the GUI for selecting an existing sizegroup.

        @param size_group: a SizeGroup for the labels
        @type size_group: gtk.SizeGroup
        """
        alignment = gtk.Alignment(1.0, 0.0, 1.0, 1.0)
        alignment.set_padding(0, 12, 48, 0)

        hbox = gtk.HBox()
        hbox.set_spacing(6)

        label = gtk.Label(('Size group:'))
        label.set_alignment(0.0, 0.5)
        size_group.add_widget(label)
        hbox.pack_start(label, False, False)

        liststore = gtk.ListStore(str, object)
        sizegroups = list(self._sizegroups.values())
        sizegroups.sort(lambda x, y: cmp(x.name, y.name))
        for group in sizegroups:
            liststore.append((group.name, group))
        self._sizegroup_combo = gtk.ComboBox(liststore)
        renderer = gtk.CellRendererText()
        self._sizegroup_combo.pack_start(renderer)
        self._sizegroup_combo.add_attribute(renderer, 'text', 0)

        self._sizegroup_combo.set_active(0)
        hbox.pack_start(self._sizegroup_combo, True, True)

        alignment.add(hbox)
        return alignment

    def _create_name_entry(self, size_group):
        """
        Create the sizegroup name entry area.

        @param size_group: a SizeGroup for the labels
        @type size_group: gtk.SizeGroup
        """
        hbox = gtk.HBox()
        hbox.set_spacing(6)

        label = gtk.Label(('Name:'))
        label.set_alignment(0.0, 0.5)
        size_group.add_widget(label)

        hbox.pack_start(label, False, False)

        self._name_entry = gtk.Entry()
        hbox.pack_start(self._name_entry, True, True)

        return hbox

    def _create_mode_entry(self, size_group):
        """
        Create the sizegroup name mode area.

        @param size_group: a SizeGroup for the labels
        @type size_group: gtk.SizeGroup
        """
        hbox = gtk.HBox()
        hbox.set_spacing(6)

        label = gtk.Label(('Mode:'))
        label.set_alignment(0.0, 0.5)
        size_group.add_widget(label)
        hbox.pack_start(label, False, False)

        liststore = gtk.ListStore(str, int)
        liststore.append((_('Horizontal'), gtk.SIZE_GROUP_HORIZONTAL))
        liststore.append((_('Vertical'), gtk.SIZE_GROUP_VERTICAL))
        liststore.append((_('Both'), gtk.SIZE_GROUP_BOTH))
        self._mode_combo = gtk.ComboBox(liststore)
        renderer = gtk.CellRendererText()
        self._mode_combo.pack_start(renderer)
        self._mode_combo.add_attribute(renderer, 'text', 0)

        self._mode_combo.set_active(0)
        hbox.pack_start(self._mode_combo, True, True)

        return hbox

    def _create_new_sizegroup_area(self, size_group):
        """
        Create the GUI for creating a new sizegroup.

        @param size_group: a SizeGroup for the labels
        @type size_group: gtk.SizeGroup
        """
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.pack_start(self._create_name_entry(size_group), False, False)
        vbox.pack_start(self._create_mode_entry(size_group), False, False)

        alignment = gtk.Alignment(1.0, 0.0, 1.0, 1.0)
        alignment.set_padding(0, 12, 48, 0)
        alignment.add(vbox)

        return alignment

    def _suggest_sizegroup_name(self):
        """
        Get a unique name suggestion for the sizegroup. It will be
        something like 'sizegroup3'.

        @return: a unique name
        @rtype: str
        """
        default_name = "sizegroup%d"
        i = 1
        while True:
            name = default_name % i
            if name not in self._sizegroups:
                return name
            i += 1

    def _on_radio_toggled(self, button, widget):
        """
        Callback that is executed when the radio buttons are
        toggled. This will enable or disable parts of the gui.

        @param button: the radio button that was toggled
        @type button: gtk.RadioButton
        @param widget: the gui element that should be enabled or disabled
        @type widget: gtk.Widget
        """
        value = button.get_active()
        widget.set_sensitive(value)

    def _on_name_entry_changed(self, entry):
        """
        Callback that is executed when the text in the name entry is
        modified.

        @param entry: the name entry
        @type entry: gtk.Entry
        """
        name = entry.get_text()
        if name in self._sizegroups:
            self._add_button.set_sensitive(False)
        else:
            self._add_button.set_sensitive(True)

class CommandAddRemoveSizeGroupGadgets(FlipFlopCommandMixin, Command):
    """
    Command for adding and removing sizegroup gadgets. When adding
    gadgets to an empty sizegroup the sizegroup will be added to the
    project. When the last gadgets is removed from a sizegroup the
    sizegroup will be removed as well.
    """

    def __init__(self, sizegroup, gadgets, project, add):
        """
        Initialize the command.

        @param sizegroup: the sizegroup that the gadgets belong to
        @type sizegroup: gazpacho.sizegroup.GSizeGroup
        @param gadgets: the gadgets that should be added or removed
        @type gadgets: list (of gazpacho.gadget.Gadget)
        @param project: the project that the sizegroup belongs to
        @type project: gazpacho.project.Project
        @param add: True if the gadgets should be added
        @type add: bool
        """
        FlipFlopCommandMixin.__init__(self, add)
        if add:
            dsc = _("Add widgets to size group '%s'") % sizegroup.name
        else:
            dsc = _("Remove widgets from size group '%s'") % sizegroup.name


        Command.__init__(self, dsc)

        self._sizegroup = sizegroup
        self._gadgets = gadgets
        self._project = project

    def _execute_add(self):
        """
        Add the gadgets to the sizegroup. This might mean that the
        sizegroup will be added as well.
        """
        if self._sizegroup.is_empty():
            self._project.add_sizegroup(self._sizegroup)

        self._sizegroup.add_gadgets(self._gadgets)
    _execute_state1 = _execute_add

    def _execute_remove(self):
        """
        Remove the gadgets from the sizegroup. This might cause the
        sizegroup to be removed as well.
        """
        self._sizegroup.remove_gadgets(self._gadgets)

        if self._sizegroup.is_empty():
            self._project.remove_sizegroup(self._sizegroup)
    _execute_state2 = _execute_remove
