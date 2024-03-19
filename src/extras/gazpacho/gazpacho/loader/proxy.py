from inspect import getmembers, ismethod

from gazpacho.loader.loader import ObjectBuilder

class Proxy(object):
    def __init__(self, gladefile=None, gladestream=None, root=None):
        self._wt = ObjectBuilder(filename=gladefile, buffer=gladestream,
                                 root=root)

        self._signal_magicconnect()

    def signal_autoconnect(self, dic):
        self._wt.signal_autoconnect(dic)

    def _signal_magicconnect(self):
        """Look for our methods to see if we need to connect any signal.
        This is copied from Kiwi."""
        actions = []
        if self._uimanager is not None:
            for a in [ag.list_actions() for ag in \
                      self._uimanager.get_action_groups()]:
                actions.extend(a)
        self._connect_methods('on_', actions)
        self._connect_methods('after_', actions)

    def _connect_methods(self, method_prefix, actions):
        methods = [m for m in getmembers(self) \
                   if ismethod(m[1]) and m[0].find(method_prefix) == 0]

        for name, method in methods:
            index = name.rfind('__')
            widget_name = name[len(method_prefix):index]
            signal_name = name[index+2:]

            try:
                # First we look in the widgets
                widget = self._wt.get_widget(widget_name)
                if not widget:
                    raise AttributeError
                if method_prefix == 'on_':
                    widget.connect(signal_name, method)
                elif method_prefix == 'after_':
                    widget.connect_after(signal_name, method)
            except AttributeError:
                # Now we try to find it in the actions
                for action in actions:
                    if widget_name == action.get_name():
                        if method_prefix == 'on_':
                            action.connect(signal_name, method)
                        elif method_prefix == 'after_':
                            action.connect_after(signal_name, method)
                        break
                else:
                    print(('Warning: the widget %s is not on my widget tree '
                           'neither in the action list') % widget_name)

    def __getattr__(self, name):
        """Easy way to access the widgets by their name."""
        return self._wt.get_widget(name)

    def get_widgets(self):
        """Returns an iterator to loop through the widgets."""
        return self._wt.widgets

    widgets = property(get_widgets)
