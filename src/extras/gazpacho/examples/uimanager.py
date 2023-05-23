import gtk

import sys

from gazpacho.loader.loader import ObjectBuilder

def on_new__activated(action):
    print 'on new'

def on_quit__activated(action):
    gtk.main_quit()

def on_window1__destroy(window):
    gtk.main_quit()

def main(args):
    wt = ObjectBuilder ('uimanager.glade')
    wt.signal_autoconnect(globals())
    if '--benchmark' in args:
        while gtk.events_pending():
            gtk.main_iteration_do()
        return

    window = wt.get_widget('window1')
    window.set_size_request(400, 300)
    window.show()
    gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
