from kiwi.ui.dialogs import info

from gazpacho.plugins import Plugin

class HelloPlugin(Plugin):

    def activate(self, app):
        self.signals = {}
        self.window = app.get_window()

        info('Hello Plugin Info: Hello Plugin activated!',
             parent=self.window)

        app.connect('set-project', self.on_app__set_project)
        app.connect('close-project', self.on_app__close_project)

    def deactivate(self):
        info('Hello Plugin Info: Hello Plugin deactivated',
             parent=self.window)

    def on_app__set_project(self, app, project):
        info('Hello Plugin Info: A new project is set: %s' % project.name,
             parent=self.window)

        # connect to anything we are interested on this project
        project.connect('changed', self.on_project__changed)

    def on_app__close_project(self, app, project):
        info('Hello Plugin Info: The project %s has been closed' %
             project.name,
             parent=self.window)

    def on_project__changed(self, project):
        info('Hello Plugin Info: The project %s has changed' % project.name,
             parent=self.window)
