import pygtk
pygtk.require('2.0')
import gtk

from sys import argv

from gazpacho.loader.loader import ObjectBuilder

def on_button1__clicked(button):
    print 'you clicked the button!'

def on_window1__destroy(window):
    gtk.main_quit()

if __name__ == '__main__':
    wt = ObjectBuilder('helloworld.glade')
    wt.signal_autoconnect(globals())
    if '--benchmark' in argv:
        while gtk.events_pending():
            gtk.main_iteration_do()
    else:
        gtk.main()

